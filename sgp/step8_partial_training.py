import pandas as pd
import geopandas as gpd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import random

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
BINNED_TRIPS = 'binned_trips_by_zone.csv'
RAW_TRIPS = 'data_trip_sum.csv'
POI_FILE = 'pois_by_zone.csv'
OUTPUT_CSV = 'step8_partial_training_results.csv'
OUTPUT_PLOT = 'step8_cpc_growth_curve.png'
CITY_CRS = 'EPSG:3414'

def calculate_global_cpc(actual_mat, pred_mat):
    intersection = np.sum(np.minimum(actual_mat, pred_mat))
    total = np.sum(actual_mat) + np.sum(pred_mat)
    return 2 * intersection / total if total > 0 else 0

def main():
    print("🚀 Step 8: Partial-Training Shell Experiment (Singapore - j != i Constraint)")
    
    # 1. Load Data
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.replace('.0', '', regex=False)
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    all_zones = gdf_utm.index.values
    z_count = len(all_zones)
    zone_to_idx = {z: i for i, z in enumerate(all_zones)}

    # Distance matrix
    coords = np.array([[p.x, p.y] for p in gdf_utm.geometry.centroid])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    
    # Load binned trips for inter-zone P(d)
    binned_df = pd.read_csv(BINNED_TRIPS)
    binned_df['ORIGIN_SUBZONE'] = binned_df['ORIGIN_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    
    # Load raw trips and parse to Matrix
    raw_df = pd.read_csv(RAW_TRIPS)
    raw_df['ORIGIN_SUBZONE'] = raw_df['ORIGIN_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    raw_df['DESTINATION_SUBZONE'] = raw_df['DESTINATION_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    
    actual_matrix = np.zeros((z_count, z_count))
    for _, row in raw_df.iterrows():
        o, d, c = row['ORIGIN_SUBZONE'], row['DESTINATION_SUBZONE'], row['COUNT']
        if o in zone_to_idx and d in zone_to_idx:
            actual_matrix[zone_to_idx[o], zone_to_idx[d]] = c
            
    internal_flows = np.diag(actual_matrix)
    external_oi = actual_matrix.sum(axis=1) - internal_flows
    
    # POI Attraction Weight
    poi_df = pd.read_csv(POI_FILE)
    poi_df['SUBZONE_C'] = poi_df['SUBZONE_C'].astype(str).str.replace('.0', '', regex=False)
    attr_map = poi_df.set_index('SUBZONE_C')['A_j'].to_dict()
    aj_vec = np.array([attr_map.get(z, 0.0) + 1.0 for z in all_zones])

    # Pre-calculate Empirical P_bin (Inter-zone)
    actual_p_bin = {}
    max_bin_limit = int(dist_mat.max()) + 1
    for z in binned_df['ORIGIN_SUBZONE'].unique():
        z_bins = binned_df[binned_df['ORIGIN_SUBZONE'] == z]
        p_vec = np.zeros(max_bin_limit + 1)
        for _, row in z_bins.iterrows():
            b, c = row['distance_bin'], row['COUNT']
            if b <= max_bin_limit: p_vec[int(b)] = c
        total = p_vec.sum()
        if total > 0: actual_p_bin[z] = p_vec / total

    # 2. Experiment Loop
    n_values = [int(z_count/i) for i in [2, 3, 4, 5, 6, 7, 8, 9, 10]]
    results = []

    for n_clusters in n_values:
        print(f"🧪 Testing N={n_clusters} clusters...")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        gdf_utm['cluster'] = kmeans.fit_predict(coords)
        cluster_groups = gdf_utm.groupby('cluster').groups
        
        iter_cpcs = []
        for i in range(20):
            # Sampling: 1 representative zone per cluster
            sampled_probs = {}
            for cid, z_ids in cluster_groups.items():
                valid_ids = [z for z in z_ids if z in actual_p_bin]
                sampled_probs[cid] = actual_p_bin[random.choice(valid_ids)] if valid_ids else None
                
            pred_matrix = np.zeros((z_count, z_count))
            for idx, z_o in enumerate(all_zones):
                # A. Ground Truth Internal
                pred_matrix[idx, idx] = internal_flows[idx]
                
                # B. Predict External
                o_out = external_oi[idx]
                if o_out == 0: continue
                
                cid = gdf_utm.loc[z_o, 'cluster']
                p_vec = sampled_probs[cid]
                if p_vec is None: continue
                
                d_bins = dist_mat[idx].astype(int)
                d_bins = np.clip(d_bins, 0, len(p_vec)-1)
                
                # Formula: (P_bin * B_j) / sum(P_bin * B_z) for z != i
                raw_probs = p_vec[d_bins] * aj_vec
                raw_probs[idx] = 0 # j != i
                
                row_sum = raw_probs.sum()
                if row_sum > 0:
                    pred_matrix[idx, :] += (raw_probs / row_sum) * o_out
            
            iter_cpcs.append(calculate_global_cpc(actual_matrix, pred_matrix))
            
        results.append({'N_clusters': n_clusters, 'Ratio': n_clusters/z_count, 'CPC': np.mean(iter_cpcs), 'STD': np.std(iter_cpcs)})

    # 3. Save & Plot
    res_df = pd.DataFrame(results)
    res_df.to_csv(OUTPUT_CSV, index=False)
    plt.figure(figsize=(10, 6))
    plt.errorbar(res_df['Ratio']*100, res_df['CPC'], yerr=res_df['STD'], fmt='-o', capsize=5, color='#2c3e50', lw=2)
    plt.title('Mobility Scale Robustness (Singapore - j != i)', fontsize=14)
    plt.xlabel('Percentage of Zones used for P(d) (%)', fontsize=12)
    plt.ylabel('Global CPC', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.savefig(OUTPUT_PLOT, dpi=300)
    print(f"✅ Step 8 complete. Results in {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
