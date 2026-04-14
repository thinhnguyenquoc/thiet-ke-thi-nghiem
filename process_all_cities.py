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
OUT_STEP7_PWR_POP = "step7_pwr_pop.csv"
OUT_STEP7_PWR_POI = "step7_pwr_poi.csv"
OUT_STEP7_EXP_POP = "step7_exp_pop.csv"
OUT_STEP7_EXP_POI = "step7_exp_poi.csv"
OUT_STEP8 = "step8_radiation_results.csv"

def calculate_metrics(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    cpc = 2 * intersection / total if total > 0 else 0
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    return cpc, mae, rmse

def main():
    if not all(os.path.exists(f) for f in [TRIPS_FILE, DIST_FILE, POI_FILE, CENSUS_FILE]):
        print("❌ Missing data files. Skipping.")
        return

    # Load data
    od_df = pd.read_csv(TRIPS_FILE)
    dist_df = pd.read_csv(DIST_FILE)
    poi_df = pd.read_csv(POI_FILE)[['idx', 'total_pois']]
    census_df = pd.read_csv(CENSUS_FILE)[['idx', 'total_population']]

    # Rename
    od_df.rename(columns={{'o_idx': 'origin', 'd_idx': 'destination', 'trip_count': 'count'}}, inplace=True)
    dist_df.rename(columns={{'o_idx': 'origin', 'd_idx': 'destination', 'distance_km': 'distance'}}, inplace=True)
    poi_df.rename(columns={{'idx': 'zone', 'total_pois': 'poi'}}, inplace=True)
    census_df.rename(columns={{'idx': 'zone', 'total_population': 'pop'}}, inplace=True)

    # 1. Binned
    merged = pd.merge(od_df, dist_df, on=['origin', 'destination'])
    merged['distance_bin'] = np.floor(merged['distance']).astype(float)
    binned = merged.groupby(['origin', 'distance_bin'])['count'].sum().reset_index()
    binned.to_csv(OUT_STEP1, index=False)

    # 3. Uniform Shell
    oi_df = od_df.groupby('origin')['count'].sum().reset_index(name='o_i')
    origin_totals = binned.groupby('origin')['count'].transform('sum')
    binned['p_bin'] = binned['count'] / (origin_totals + 1e-9)
    full_pairs = dist_df.copy()
    full_pairs['distance_bin'] = np.floor(full_pairs['distance']).astype(float)
    nk_df = full_pairs.groupby(['origin', 'distance_bin']).size().reset_index(name='n_k')
    step3_df = pd.merge(full_pairs, oi_df, on='origin')
    step3_df = pd.merge(step3_df, binned[['origin', 'distance_bin', 'p_bin']], on=['origin', 'distance_bin'], how='left').fillna(0)
    step3_df = pd.merge(step3_df, nk_df, on=['origin', 'distance_bin'])
    step3_df['pred_count'] = step3_df['o_i'] * step3_df['p_bin'] / step3_df['n_k']
    step3_df[['origin', 'destination', 'pred_count']].to_csv(OUT_STEP3, index=False)

    # 4. Weighted Shell
    step4_df = pd.merge(pd.merge(full_pairs, oi_df, on='origin'), binned[['origin', 'distance_bin', 'p_bin']], on=['origin', 'distance_bin'], how='left').fillna(0)
    step4_df = pd.merge(step4_df, poi_df.rename(columns={{'zone': 'destination'}}), on='destination')
    sum_aj = step4_df.groupby(['origin', 'distance_bin'])['poi'].sum().reset_index(name='sum_aj')
    step4_df = pd.merge(step4_df, sum_aj, on=['origin', 'distance_bin'])
    step4_df['pred_count'] = np.where(step4_df['sum_aj'] > 0, step4_df['o_i'] * step4_df['p_bin'] * (step4_df['poi'] / step4_df['sum_aj']), 0)
    step4_df[['origin', 'destination', 'pred_count']].to_csv(OUT_STEP4, index=False)

    # 6 & 8. Radiation
    def run_rad(base_df, mass_col):
        rad = pd.merge(dist_df, oi_df, on='origin')
        rad = pd.merge(rad, base_df.rename(columns={{'zone': 'origin', mass_col: 'm_i'}}), on='origin')
        rad = pd.merge(rad, base_df.rename(columns={{'zone': 'destination', mass_col: 'n_j'}}), on='destination')
        all_res = []
        for _, g in rad.groupby('origin'):
            g = g.sort_values('distance')
            g['s_ij'] = g['n_j'].cumsum().shift(1).fillna(0)
            g['pred_count'] = g['o_i'] * (g['m_i'] * g['n_j']) / ((g['m_i'] + g['s_ij'] + 1e-6) * (g['m_i'] + g['n_j'] + g['s_ij'] + 1e-6))
            all_res.append(g[['origin', 'destination', 'pred_count']])
        return pd.concat(all_res)
    
    run_rad(census_df, 'pop').to_csv(OUT_STEP6, index=False)
    run_rad(poi_df, 'poi').to_csv(OUT_STEP8, index=False)

    # 7. Gravity Optimization
    all_zones = sorted(census_df['zone'].unique())
    pop_vec = census_df.set_index('zone').loc[all_zones, 'pop'].values
    poi_vec = poi_df.set_index('zone').loc[all_zones, 'poi'].values
    zone_to_idx = {{z: i for i, z in enumerate(all_zones)}}
    actual_mat = np.zeros((len(all_zones), len(all_zones)))
    for _, row in od_df.iterrows():
        if row['origin'] in zone_to_idx and row['destination'] in zone_to_idx:
            actual_mat[zone_to_idx[row['origin']], zone_to_idx[row['destination']]] = row['count']
    dist_mat = np.zeros((len(all_zones), len(all_zones)))
    for _, row in dist_df.iterrows():
        if row['origin'] in zone_to_idx and row['destination'] in zone_to_idx:
            dist_mat[zone_to_idx[row['origin']], zone_to_idx[row['destination']]] = row['distance']
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat)

    def solve_grav(gamma, attr, ftype):
        decay = (attr / (dist_mat ** gamma)) if ftype == 'power' else (attr * np.exp(-gamma * dist_mat))
        row_sums = decay.sum(axis=1, keepdims=True); row_sums[row_sums == 0] = 1.0
        return (decay / row_sums) * actual_mat.sum(axis=1, keepdims=True)

    def obj(gamma, attr, ftype):
        p = solve_grav(gamma[0], attr, ftype)
        it = np.sum(np.minimum(actual_mat, p)); tot = np.sum(actual_mat) + np.sum(p)
        return 1.0 - (2 * it / tot if tot > 0 else 0)

    scenarios = [('Power-Pop', pop_vec, 'power', [1.5], OUT_STEP7_PWR_POP),
                 ('Power-POI', poi_vec, 'power', [1.5], OUT_STEP7_PWR_POI),
                 ('Exp-Pop', pop_vec, 'exponential', [0.1], OUT_STEP7_EXP_POP),
                 ('Exp-POI', poi_vec, 'exponential', [0.1], OUT_STEP7_EXP_POI)]
    
    model_summaries = []
    for name, attr, ftype, x0, out_f in scenarios:
        res = minimize(obj, x0=x0, args=(attr, ftype), bounds=[(0, 5)])
        p_mat = solve_grav(res.x[0], attr, ftype)
        it = np.sum(np.minimum(actual_mat, p_mat)); tot = np.sum(actual_mat) + np.sum(p_mat)
        model_summaries.append({{'Model': name, 'CPC': 2*it/tot}})

    # Add other models to summary
    others = [('Attraction-Uniform', OUT_STEP3), ('Attraction-Weighted', OUT_STEP4), 
              ('Radiation-Pop', OUT_STEP6), ('Radiation-POI', OUT_STEP8)]
    for name, f in others:
        m_df = pd.read_csv(f)
        merged_m = pd.merge(m_df, od_df, on=['origin', 'destination'], how='left').fillna(0)
        it = np.sum(np.minimum(merged_m['count'], merged_m['pred_count']))
        tot = np.sum(merged_m['count']) + np.sum(merged_m['pred_count'])
        model_summaries.append({{'Model': name, 'CPC': 2*it/tot if tot > 0 else 0}})
    
    pd.DataFrame(model_summaries).to_csv('final_summary_report.csv', index=False)

if __name__ == "__main__":
    main()

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
