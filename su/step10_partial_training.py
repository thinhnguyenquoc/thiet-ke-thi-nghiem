import pandas as pd
import geopandas as gpd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import random

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
BINNED_TRIPS = 'binned_trips_by_zone.csv'
RAW_TRIPS = 'aggregated_trips.csv'
POI_FILE = 'pois_by_zone.csv'
OUTPUT_CSV = 'step10_partial_training_results.csv'
OUTPUT_PLOT = 'step10_cpc_growth_curve.png'
CITY_CRS = 'EPSG:5179'

def calculate_global_cpc(actual_df, pred_matrix, all_zones):
    """Calculates Global CPC using matrix operations for speed."""
    zone_to_idx = {z: i for i, z in enumerate(all_zones)}
    actual_matrix = np.zeros((len(all_zones), len(all_zones)))
    
    for _, row in actual_df.iterrows():
        o, d, count = str(row['ORIGIN_SUBZONE']).replace('.0',''), str(row['DESTINATION_SUBZONE']).replace('.0',''), row['COUNT']
        if o in zone_to_idx and d in zone_to_idx:
            actual_matrix[zone_to_idx[o], zone_to_idx[d]] = count
            
    intersection = np.sum(np.minimum(actual_matrix, pred_matrix))
    total = np.sum(actual_matrix) + np.sum(pred_matrix)
    return 2 * intersection / total if total > 0 else 0

def main():
    print("🚀 Step 10: Partial-Training Shell Experiment (Seoul - Random Selection)...")
    
    # 1. Load Data
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.replace('.0', '', regex=False)
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    gdf_utm['cx'] = gdf_utm.geometry.centroid.x
    gdf_utm['cy'] = gdf_utm.geometry.centroid.y

    print("📖 Loading binned trips for P(d)...")
    binned_df = pd.read_csv(BINNED_TRIPS)
    binned_df['ORIGIN_SUBZONE'] = binned_df['ORIGIN_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    
    print("📖 Loading raw trips for CPC validation...")
    raw_df = pd.read_csv(RAW_TRIPS)
    raw_df['ORIGIN_SUBZONE'] = raw_df['ORIGIN_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    raw_df['DESTINATION_SUBZONE'] = raw_df['DESTINATION_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    
    poi_df = pd.read_csv(POI_FILE)
    poi_df['SUBZONE_C'] = poi_df['SUBZONE_C'].astype(str).str.replace('.0', '', regex=False)
    attr_dict = poi_df.set_index('SUBZONE_C')['A_j'].to_dict()

    all_zones = gdf_utm.index.values
    z_count = len(all_zones)
    
    # Pre-calculate Distance Matrix and A_j vector
    coords = gdf_utm[['cx', 'cy']].values
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat)
    aj_vec = np.array([attr_dict.get(z, 0.0) + 1.0 for z in all_zones])

    # Pre-calculate Actual P_bin for ALL zones
    print("📊 Pre-calculating empirical P_bin from binned data...")
    actual_p_bin = {}
    max_bin_limit = int(dist_mat.max()) + 1
    for z in all_zones:
        z_bins = binned_df[binned_df['ORIGIN_SUBZONE'] == z]
        if z_bins.empty:
            actual_p_bin[z] = None
            continue
        p_vec = np.zeros(max_bin_limit + 1)
        for _, row in z_bins.iterrows():
            b, c = row['distance_bin'], row['COUNT']
            if b <= max_bin_limit: p_vec[int(b)] = c
        total = p_vec.sum()
        actual_p_bin[z] = p_vec / total if total > 0 else None

    oi_dict = raw_df.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()

    # 2. Experiment Loop
    n_values = [int(z_count/i) for i in [2, 3, 4, 5, 6, 7, 8, 9, 10]]
    results = []

    for n_clusters in n_values:
        print(f"🧪 Testing N={n_clusters} clusters (sampling 1 random zone/cluster)...")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        gdf_utm['cluster'] = kmeans.fit_predict(coords)
        cluster_groups = gdf_utm.groupby('cluster').groups
        
        iter_cpcs = []
        for i in range(20):
            sampled_probs = {}
            for cid, z_indices in cluster_groups.items():
                valid_indices = [z for z in z_indices if actual_p_bin.get(z) is not None]
                if not valid_indices:
                    sampled_probs[cid] = None
                else:
                    rep_zone = random.choice(valid_indices)
                    sampled_probs[cid] = actual_p_bin[rep_zone]
                
            pred_matrix = np.zeros((z_count, z_count))
            for idx, z_o in enumerate(all_zones):
                cid = gdf_utm.loc[z_o, 'cluster']
                p_vec = sampled_probs[cid]
                if p_vec is None: continue
                
                o_total = oi_dict.get(z_o, 0)
                d_bins = dist_mat[idx].astype(int)
                d_bins = np.clip(d_bins, 0, len(p_vec)-1)
                
                raw_probs = p_vec[d_bins] * aj_vec
                row_sum = raw_probs.sum()
                if row_sum > 0:
                    pred_matrix[idx, :] = (raw_probs / row_sum) * o_total
            
            cpc = calculate_global_cpc(raw_df, pred_matrix, all_zones)
            iter_cpcs.append(cpc)
            
        avg_cpc = np.mean(iter_cpcs)
        std_cpc = np.std(iter_cpcs)
        print(f"   -> Average CPC: {avg_cpc:.4f} (std: {std_cpc:.4f})")
        results.append({'N_clusters': n_clusters, 'Ratio': n_clusters/z_count, 'CPC': avg_cpc, 'STD': std_cpc})

    # 3. Save & Plot
    res_df = pd.DataFrame(results)
    res_df.to_csv(OUTPUT_CSV, index=False)
    
    plt.figure(figsize=(10, 6))
    plt.errorbar(res_df['Ratio']*100, res_df['CPC'], yerr=res_df['STD'], fmt='-o', capsize=5, color='#e67e22', lw=2)
    plt.title('Mobility Scale Robustness (Seoul)', fontsize=14)
    plt.xlabel('Percentage of Zones used for P(d) (%)', fontsize=12)
    plt.ylabel('Global CPC', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.savefig(OUTPUT_PLOT, dpi=300)
    print(f"✅ Step 10 complete. Results in {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
