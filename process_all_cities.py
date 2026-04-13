import os
import pandas as pd
import numpy as np
import subprocess
from scipy.optimize import minimize

# Paths
BASE_DIR = os.getcwd()
DATA_DIR_ROOT = os.path.join(BASE_DIR, "cityDataset_real")
OUTPUT_DIR_ROOT = os.path.join(BASE_DIR, "cities")

# Template for execute_steps.py
EXECUTE_STEPS_TEMPLATE = """import pandas as pd
import numpy as np
import os
from scipy.optimize import minimize

# Paths
DATA_DIR = "{data_dir}"
TRIPS_FILE = os.path.join(DATA_DIR, "pairs/od.csv")
DIST_FILE = os.path.join(DATA_DIR, "pairs/distance.csv")
POI_FILE = os.path.join(DATA_DIR, "nodes/poi.csv")
CENSUS_FILE = os.path.join(DATA_DIR, "nodes/census.csv")

# Output files
OUT_STEP1 = "binned_trips_by_zone.csv"
OUT_STEP3 = "step3_gravity_results.csv"
OUT_STEP4 = "step4_gravity_results.csv"
OUT_STEP6 = "step6_radiation_results.csv"
OUT_STEP7 = "step7_gravity_results.csv"
OUT_STEP8 = "step8_radiation_results.csv"
OUT_STEP7_EXP = "step7b_gravity_exp_results.csv"

def calculate_metrics(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    cpc = 2 * intersection / total if total > 0 else 0
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    return cpc, r2, mae, rmse

def main():
    if not all(os.path.exists(f) for f in [TRIPS_FILE, DIST_FILE, POI_FILE, CENSUS_FILE]):
        print("❌ Missing essential data files. Skipping.")
        return

    # Load data
    od_df = pd.read_csv(TRIPS_FILE)
    dist_df = pd.read_csv(DIST_FILE)
    poi_df = pd.read_csv(POI_FILE)[['idx', 'total_pois']]
    census_df = pd.read_csv(CENSUS_FILE)[['idx', 'total_population']]

    # Rename columns for consistency
    od_df.rename(columns={{'o_idx': 'origin', 'd_idx': 'destination', 'trip_count': 'count'}}, inplace=True)
    dist_df.rename(columns={{'o_idx': 'origin', 'd_idx': 'destination', 'distance_km': 'distance'}}, inplace=True)
    poi_df.rename(columns={{'idx': 'zone', 'total_pois': 'poi'}}, inplace=True)
    census_df.rename(columns={{'idx': 'zone', 'total_population': 'pop'}}, inplace=True)

    # 1. Histograms
    merged = pd.merge(od_df, dist_df, on=['origin', 'destination'])
    merged['distance_bin'] = np.floor(merged['distance']).astype(float)
    binned = merged.groupby(['origin', 'distance_bin'])['count'].sum().reset_index()
    binned.to_csv(OUT_STEP1, index=False)

    # 3. Uniform Shell
    oi_df = od_df.groupby('origin')['count'].sum().reset_index(name='o_i')
    origin_totals = binned.groupby('origin')['count'].transform('sum')
    binned['p_bin'] = binned['count'] / origin_totals
    full_pairs = dist_df.copy()
    full_pairs['distance_bin'] = np.floor(full_pairs['distance']).astype(float)
    nk_df = full_pairs.groupby(['origin', 'distance_bin']).size().reset_index(name='n_k')
    step3_df = pd.merge(full_pairs, oi_df, on='origin')
    step3_df = pd.merge(step3_df, binned[['origin', 'distance_bin', 'p_bin']], on=['origin', 'distance_bin'], how='left')
    step3_df['p_bin'] = step3_df['p_bin'].fillna(0)
    step3_df = pd.merge(step3_df, nk_df, on=['origin', 'distance_bin'])
    step3_df['pred_count'] = step3_df['o_i'] * step3_df['p_bin'] / step3_df['n_k']
    final_step3 = pd.merge(step3_df, od_df, on=['origin', 'destination'], how='left').fillna(0)
    final_step3[['origin', 'destination', 'count', 'pred_count']].to_csv(OUT_STEP3, index=False)

    # 4. POI-Weighted Shell
    step4_df = pd.merge(step3_df.drop(columns=['pred_count', 'n_k']), poi_df.rename(columns={{'zone': 'destination'}}), on='destination')
    sum_aj_df = step4_df.groupby(['origin', 'distance_bin'])['poi'].sum().reset_index(name='sum_aj')
    step4_df = pd.merge(step4_df, sum_aj_df, on=['origin', 'distance_bin'])
    step4_df['pred_count'] = np.where(step4_df['sum_aj'] > 0, 
                                     step4_df['o_i'] * step4_df['p_bin'] * (step4_df['poi'] / step4_df['sum_aj']),
                                     0)
    final_step4 = pd.merge(step4_df, od_df, on=['origin', 'destination'], how='left').fillna(0)
    final_step4[['origin', 'destination', 'count', 'pred_count']].to_csv(OUT_STEP4, index=False)

    # 6. Radiation (Pop)
    rad_df = pd.merge(dist_df, oi_df, on='origin')
    rad_df = pd.merge(rad_df, census_df.rename(columns={{'zone': 'origin', 'pop': 'm_i'}}), on='origin')
    rad_df = pd.merge(rad_df, census_df.rename(columns={{'zone': 'destination', 'pop': 'n_j'}}), on='destination')
    all_s_ij = []
    for origin, group in rad_df.groupby('origin'):
        group = group.sort_values('distance')
        group['cum_pop'] = group['n_j'].cumsum()
        group['s_ij'] = group['cum_pop'].shift(1).fillna(0)
        all_s_ij.append(group)
    rad_df = pd.concat(all_s_ij)
    rad_df['pred_count'] = rad_df['o_i'] * (rad_df['m_i'] * rad_df['n_j']) / \\
                           ((rad_df['m_i'] + rad_df['s_ij'] + 1e-6) * (rad_df['m_i'] + rad_df['n_j'] + rad_df['s_ij'] + 1e-6))
    final_rad = pd.merge(rad_df, od_df, on=['origin', 'destination'], how='left').fillna(0)
    final_rad[['origin', 'destination', 'count', 'pred_count']].to_csv(OUT_STEP6, index=False)

    # 7. Production-Constrained Gravity
    all_zones = sorted(census_df['zone'].unique())
    pop_vec = census_df.set_index('zone').loc[all_zones, 'pop'].values
    actual_mat = np.zeros((len(all_zones), len(all_zones)))
    zone_to_idx = {{z: i for i, z in enumerate(all_zones)}}
    for _, row in od_df.iterrows():
        if row['origin'] in zone_to_idx and row['destination'] in zone_to_idx:
            actual_mat[zone_to_idx[row['origin']], zone_to_idx[row['destination']]] = row['count']
    dist_mat = np.zeros((len(all_zones), len(all_zones)))
    for _, row in dist_df.iterrows():
        if row['origin'] in zone_to_idx and row['destination'] in zone_to_idx:
            dist_mat[zone_to_idx[row['origin']], zone_to_idx[row['destination']]] = row['distance']
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat)

    def solve_gravity(gamma, type='power'):
        decay = (pop_vec / (dist_mat ** gamma)) if type == 'power' else (pop_vec * np.exp(-gamma * dist_mat))
        row_sums = decay.sum(axis=1, keepdims=True); row_sums[row_sums == 0] = 1.0
        prob_mat = decay / row_sums
        return prob_mat * actual_mat.sum(axis=1, keepdims=True)

    def objective(gamma, type='power'):
        pred = solve_gravity(gamma[0], type)
        it = np.sum(np.minimum(actual_mat, pred)); tot = np.sum(actual_mat) + np.sum(pred)
        return 1.0 - (2 * it / tot if tot > 0 else 0)

    res_p = minimize(objective, x0=[1.5], args=('power',), bounds=[(0, 5)])
    pred_p = solve_gravity(res_p.x[0], 'power')
    res_e = minimize(objective, x0=[0.1], args=('exponential',), bounds=[(0, 5)])
    pred_e = solve_gravity(res_e.x[0], 'exponential')

    def mat_to_df(mat):
        rows = []
        for i, o in enumerate(all_zones):
            for j, d in enumerate(all_zones):
                rows.append({{'origin': o, 'destination': d, 'pred_count': mat[i, j]}})
        return pd.merge(pd.DataFrame(rows), od_df, on=['origin', 'destination'], how='left').fillna(0)

    mat_to_df(pred_p)[['origin', 'destination', 'count', 'pred_count']].to_csv(OUT_STEP7, index=False)
    mat_to_df(pred_e)[['origin', 'destination', 'count', 'pred_count']].to_csv(OUT_STEP7_EXP, index=False)

    # 8. Radiation (POI)
    rad_poi_df = pd.merge(dist_df, oi_df, on='origin')
    rad_poi_df = pd.merge(rad_poi_df, poi_df.rename(columns={{'zone': 'origin', 'poi': 'm_i'}}), on='origin')
    rad_poi_df = pd.merge(rad_poi_df, poi_df.rename(columns={{'zone': 'destination', 'poi': 'n_j'}}), on='destination')
    all_s_ij_poi = []
    for origin, group in rad_poi_df.groupby('origin'):
        group = group.sort_values('distance')
        group['cum_poi'] = group['n_j'].cumsum()
        group['s_ij'] = group['cum_poi'].shift(1).fillna(0)
        all_s_ij_poi.append(group)
    rad_poi_df = pd.concat(all_s_ij_poi)
    rad_poi_df['pred_count'] = rad_poi_df['o_i'] * (rad_poi_df['m_i'] * rad_poi_df['n_j']) / \\
                               ((rad_poi_df['m_i'] + rad_poi_df['s_ij'] + 1e-6) * (rad_poi_df['m_i'] + rad_poi_df['n_j'] + rad_poi_df['s_ij'] + 1e-6))
    pd.merge(rad_poi_df, od_df, on=['origin', 'destination'], how='left').fillna(0)[['origin', 'destination', 'count', 'pred_count']].to_csv(OUT_STEP8, index=False)

    # Final Summary
    model_files = {{'Attraction-Uniform': OUT_STEP3, 'Attraction-Weighted': OUT_STEP4, 'Radiation-Pop': OUT_STEP6, 'Radiation-POI': OUT_STEP8, 'Power-Decay': OUT_STEP7, 'Exponential-Decay': OUT_STEP7_EXP}}
    summary_rows = []
    for name, f in model_files.items():
        if os.path.exists(f):
            m_df = pd.read_csv(f)
            _, r2, mae, rmse = calculate_metrics(m_df['count'], m_df['pred_count'])
            cpcs = []
            for origin, group in m_df.groupby('origin'):
                t, p = group['count'].values, group['pred_count'].values
                if (t.sum() + p.sum()) > 0: cpcs.append(2 * np.sum(np.minimum(t, p)) / (t.sum() + p.sum()))
            summary_rows.append({{'Model': name, 'CPC': np.mean(cpcs) if cpcs else 0, 'R2': r2, 'MAE': mae, 'RMSE': rmse}})
    pd.DataFrame(summary_rows).to_csv('final_summary_report.csv', index=False)

if __name__ == "__main__":
    main()
"""

def main():
    cities = [d for d in os.listdir(DATA_DIR_ROOT) if os.path.isdir(os.path.join(DATA_DIR_ROOT, d))]
    print(f"🏙️ Found {len(cities)} cities in cityDataset_real.")
    
    overall_summary = []

    for city in sorted(cities):
        print(f"--- Processing {city} ---")
        city_out_dir = os.path.join(OUTPUT_DIR_ROOT, city)
        os.makedirs(city_out_dir, exist_ok=True)
        
        # Write execute_steps.py for this city
        script_path = os.path.join(city_out_dir, "execute_steps.py")
        data_dir_abs = os.path.join(DATA_DIR_ROOT, city)
        with open(script_path, "w") as f:
            f.write(EXECUTE_STEPS_TEMPLATE.format(data_dir=data_dir_abs))
        
        # Run it
        try:
            subprocess.run(["python3", "execute_steps.py"], cwd=city_out_dir, capture_output=True, text=True)
            
            # Read back summary
            summary_path = os.path.join(city_out_dir, "final_summary_report.csv")
            if os.path.exists(summary_path):
                sum_df = pd.read_csv(summary_path)
                sum_df['City'] = city
                overall_summary.append(sum_df)
                best_model = sum_df.loc[sum_df['CPC'].idxmax()]
                print(f"✅ Done {city}. Best: {best_model['Model']} (CPC: {best_model['CPC']:.4f})")
            else:
                print(f"⚠️ {city} failed to produce summary.")
        except Exception as e:
            print(f"❌ Error processing {city}: {e}")

    if overall_summary:
        final_all_df = pd.concat(overall_summary)
        final_all_df.to_csv("FINAL_ALL_CITIES_REPORT.csv", index=False)
        print("\n🏆 ALL CITIES PROCESSED. Master report saved as FINAL_ALL_CITIES_REPORT.csv")

if __name__ == "__main__":
    main()
