import os
import pandas as pd
import numpy as np
import subprocess
from scipy.optimize import minimize

# Paths
BASE_DIR = os.getcwd()
DATA_DIR_ROOT = os.path.join(BASE_DIR, "cityDataset_real")
OUTPUT_DIR_ROOT = os.path.join(BASE_DIR, "cities")

# Template for execute_steps.py (Updated for j != i and Ground Truth diagonals)
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
    return cpc

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

    # 0. Matrix Setup (j != i and Internal Flows as Ground Truth)
    all_zones = sorted(census_df['zone'].unique())
    z_count = len(all_zones)
    zone_to_idx = {{z: i for i, z in enumerate(all_zones)}}
    
    actual_mat = np.zeros((z_count, z_count))
    for _, row in od_df.iterrows():
        if row['origin'] in zone_to_idx and row['destination'] in zone_to_idx:
            actual_mat[zone_to_idx[row['origin']], zone_to_idx[row['destination']]] = row['count']
    
    internal_flows = np.diag(actual_mat)
    external_oi = actual_mat.sum(axis=1) - internal_flows
    
    dist_mat = np.zeros((z_count, z_count))
    for _, row in dist_df.iterrows():
        if row['origin'] in zone_to_idx and row['destination'] in zone_to_idx:
            dist_mat[zone_to_idx[row['origin']], zone_to_idx[row['destination']]] = row['distance']
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat)

    # 1. P(bin|i) - Binned Probability Distribution (Inter-zone only)
    ext_trips = od_df[od_df['origin'] != od_df['destination']].copy()
    ext_trips = pd.merge(ext_trips, dist_df, on=['origin', 'destination'])
    ext_trips['bin'] = np.floor(ext_trips['distance']).astype(int)
    
    binned_counts = ext_trips.groupby(['origin', 'bin'])['count'].sum().reset_index()
    origin_ext_sum = binned_counts.groupby('origin')['count'].transform('sum')
    binned_counts['p_bin'] = binned_counts['count'] / (origin_ext_sum + 1e-9)
    binned_counts.to_csv(OUT_STEP1, index=False)
    
    p_bin_dict = {{}}
    for _, row in binned_counts.iterrows():
        if row['origin'] not in p_bin_dict: p_bin_dict[row['origin']] = {{}}
        p_bin_dict[row['origin']][row['bin']] = row['p_bin']

    # 3 & 4. Shell Models
    def predict_shell(mode='uniform'):
        pred = np.zeros((z_count, z_count))
        poi_dict = poi_df.set_index('zone')['poi'].to_dict()
        epsilon = 1.0
        
        for i_idx, origin in enumerate(all_zones):
            o_out = external_oi[i_idx]
            if o_out == 0: continue
            
            # Destination info for this origin
            dists = dist_mat[i_idx]
            bins = np.floor(dists).astype(int)
            p_dict = p_bin_dict.get(origin, {{}})
            
            for b, prob in p_dict.items():
                if prob == 0: continue
                # dests in this bin (j != i)
                in_bin = (bins == b) & (np.arange(z_count) != i_idx)
                if not np.any(in_bin): continue
                
                if mode == 'uniform':
                    weights = in_bin.astype(float)
                else:
                    weights = np.array([poi_dict.get(all_zones[j], 0) + epsilon if in_bin[j] else 0 for j in range(z_count)])
                
                ws = weights.sum()
                if ws > 0:
                    pred[i_idx] += (weights / ws) * (o_out * prob)
        
        return pred + np.diag(internal_flows)

    m_uniform = predict_shell('uniform')
    m_weighted = predict_shell('weighted')
    
    def save_mat(m, f):
        rows = []
        for i, o in enumerate(all_zones):
            for j, d in enumerate(all_zones):
                if m[i,j] > 0: rows.append({{'origin': o, 'destination': d, 'pred_count': m[i,j]}})
        pd.DataFrame(rows).to_csv(f, index=False)

    save_mat(m_uniform, OUT_STEP3)
    save_mat(m_weighted, OUT_STEP4)

    # 6 & 8. Radiation
    def run_rad(mass_vec):
        pred = np.zeros((z_count, z_count))
        for i in range(z_count):
            o_out = external_oi[i]
            if o_out == 0: continue
            m_i = mass_vec[i]
            dists = dist_mat[i]
            mass_j = mass_vec.copy()
            # Sort by distance
            order = np.argsort(dists)
            sorted_mass = mass_j[order]
            s_ij = np.cumsum(sorted_mass) - sorted_mass # s_ij does not include j
            # But standard radiation s_ij is mass in circle *excluding* i and j
            # So s_ij_actual = cumsum(mass) - mass_i - mass_j
            # For simplicity using the cumul search:
            sorted_s = np.array([mass_j[dists < dists[idx]].sum() - m_i for idx in range(z_count)])
            sorted_s = np.where(sorted_s < 0, 0, sorted_s)
            
            p_ij_num = m_i * mass_j
            p_ij_den = (m_i + sorted_s) * (m_i + mass_j + sorted_s)
            p_ij = np.where(p_ij_den > 0, p_ij_num / p_ij_den, 0)
            p_ij[i] = 0 # j != i
            
            if p_ij.sum() > 0:
                pred[i] = (p_ij / p_ij.sum()) * o_out
                
        return pred + np.diag(internal_flows)

    pop_vec = census_df.set_index('zone').loc[all_zones, 'pop'].values + 1.0
    poi_vec = poi_df.set_index('zone').loc[all_zones, 'poi'].values + 1.0
    
    save_mat(run_rad(pop_vec), OUT_STEP6)
    save_mat(run_rad(poi_vec), OUT_STEP8)

    # 7. Gravity
    def solve_grav(gamma, attr, ftype):
        decay = (1.0 / (dist_mat ** gamma)) if ftype == 'power' else np.exp(-gamma * dist_mat)
        weight_mat = decay * attr[np.newaxis, :]
        np.fill_diagonal(weight_mat, 0)
        row_sums = weight_mat.sum(axis=1, keepdims=True); row_sums[row_sums == 0] = 1.0
        prob_mat = weight_mat / row_sums
        return (prob_mat * external_oi[:, np.newaxis]) + np.diag(internal_flows)

    def obj(gamma, attr, ftype):
        p = solve_grav(gamma[0], attr, ftype)
        it = np.sum(np.minimum(actual_mat, p)); tot = np.sum(actual_mat) + np.sum(p)
        return 1.0 - (2 * it / tot if tot > 0 else 0)

    model_summaries = []
    scenarios = [('Power-Pop', pop_vec, 'power'), ('Power-POI', poi_vec, 'power'),
                 ('Exp-Pop', pop_vec, 'exp'), ('Exp-POI', poi_vec, 'exp')]
    
    for name, attr, ftype in scenarios:
        res = minimize(obj, x0=[1.0], args=(attr, ftype), bounds=[(0.01, 5)])
        p_mat = solve_grav(res.x[0], attr, ftype)
        model_summaries.append({{'Model': name, 'CPC': 1.0 - res.fun, 'Params': res.x[0]}})

    # Eval others
    others = [('Uniform', m_uniform), ('Weighted', m_weighted), 
              ('Rad-Pop', run_rad(pop_vec)), ('Rad-POI', run_rad(poi_vec))]
    for name, mat in others:
        it = np.sum(np.minimum(actual_mat, mat)); tot = np.sum(actual_mat) + np.sum(mat)
        model_summaries.append({{'Model': name, 'CPC': 2*it/tot if tot > 0 else 0, 'Params': 0}})
    
    pd.DataFrame(model_summaries).to_csv('final_summary_report.csv', index=False)

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
            result = subprocess.run(["python3", "execute_steps.py"], cwd=city_out_dir, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Error in {city}: {result.stderr}")
            
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
            print(f"❌ Exception processing {city}: {e}")

    if overall_summary:
        final_all_df = pd.concat(overall_summary)
        # Reorder columns: City, Model, CPC, Params
        final_all_df = final_all_df[['City', 'Model', 'CPC', 'Params']]
        final_all_df.to_csv("FINAL_ALL_CITIES_REPORT.csv", index=False)
        print("\n🏆 ALL CITIES PROCESSED. Master report saved as FINAL_ALL_CITIES_REPORT.csv")

if __name__ == "__main__":
    main()
