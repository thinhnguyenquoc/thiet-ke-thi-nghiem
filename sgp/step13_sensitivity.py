import pandas as pd
import geopandas as gpd
import numpy as np
import os
import random
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BINNED_FILE = os.path.join(CURRENT_DIR, 'binned_trips_by_zone.csv')
SZ_SHAPEFILE = os.path.join(CURRENT_DIR, 'sub_zone/data_sgp_subzone.shp')
POI_FILE = os.path.join(CURRENT_DIR, 'pois_by_zone.csv')
TRIP_FILE = os.path.join(CURRENT_DIR, 'data_trip_sum.csv')
OUTPUT_FILE = os.path.join(CURRENT_DIR, 'step13_subzone_sensitivity_results.csv')
CITY_CRS = 'EPSG:3414'
N_CLUSTERS = 10
RATIOS = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01]
N_ITERATIONS = 20

def calculate_origin_averaged_cpc(real_df, pred_df):
    unique_origins = real_df['ORIGIN_SUBZONE'].unique()
    cpcs = []
    real_gb = real_df.groupby('ORIGIN_SUBZONE')
    pred_gb = pred_df.groupby('ORIGIN_SUBZONE')
    for origin in unique_origins:
        if origin not in pred_gb.groups:
            continue
        r_z = real_gb.get_group(origin)[['DEST_SUBZONE', 'COUNT']]
        p_z = pred_gb.get_group(origin)[['DEST_SUBZONE', 'T_hat_ij']]
        merged = pd.merge(r_z, p_z, on='DEST_SUBZONE', how='outer').fillna(0)
        y_true = merged['COUNT'].values
        y_pred = merged['T_hat_ij'].values
        intersection = np.sum(np.minimum(y_true, y_pred))
        total = np.sum(y_true) + np.sum(y_pred)
        cpcs.append(2.0 * intersection / total if total > 0 else 0.0)
    return np.mean(cpcs) if cpcs else 0.0

def main():
    print(f"🚀 Step 13: Comprehensive Sensitivity Analysis (Singapore)...")

    # 1. Load Data
    binned_df = pd.read_csv(BINNED_FILE)
    poi_df = pd.read_csv(POI_FILE)
    gdf = gpd.read_file(SZ_SHAPEFILE).to_crs(CITY_CRS)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str)
    gdf['centroid'] = gdf.geometry.centroid
    coords = np.array([[c.x, c.y] for c in gdf['centroid']])

    # 2. Clusters
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    gdf['cluster'] = kmeans.fit_predict(coords)

    subzone_ids = gdf['SUBZONE_C'].values
    aj_values = gdf.merge(poi_df[['SUBZONE_C', 'A_j']], on='SUBZONE_C', how='left').fillna(0)['A_j'].values
    all_centroids = np.array([[c.x, c.y] for c in gdf['centroid']])
    unique_origins = binned_df['ORIGIN_SUBZONE'].unique()
    zone_to_idx = {z: i for i, z in enumerate(subzone_ids)}
    
    real_trips = pd.read_csv(TRIP_FILE)[['ORIGIN_SUBZONE', 'DESTINATION_SUBZONE', 'COUNT']]
    real_trips.rename(columns={'DESTINATION_SUBZONE': 'DEST_SUBZONE'}, inplace=True)
    real_trips['ORIGIN_SUBZONE'] = real_trips['ORIGIN_SUBZONE'].astype(str)
    
    binned_df['ORIGIN_SUBZONE'] = binned_df['ORIGIN_SUBZONE'].astype(str)
    binned_df['P_bin_k_i'] = binned_df.groupby('ORIGIN_SUBZONE')['COUNT'].transform(lambda x: x / x.sum())

    # Precompute spatial bins
    print("📏 Precomputing spatial bins...")
    origin_spatial_cache = {}
    for origin_zone in unique_origins:
        origin_zone_str = str(origin_zone)
        if origin_zone_str not in zone_to_idx: continue
        origin_idx = zone_to_idx[origin_zone_str]
        origin_pos = all_centroids[origin_idx]
        dists = np.sqrt(np.sum((all_centroids - origin_pos)**2, axis=1)) / 1000.0
        bins = np.floor(dists).astype(int)
        local_df = pd.DataFrame({'bin_k': bins, 'A_j': aj_values})
        bin_sums = local_df.groupby('bin_k')['A_j'].sum().to_dict()
        origin_spatial_cache[origin_zone_str] = {
            'bins': bins,
            'sum_az_list': [bin_sums[b] if b in bin_sums else 0 for b in bins],
            'o_i': binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone_str]['COUNT'].sum()
        }

    # 3. Sensitivity Loop
    results_record = []
    for ratio in RATIOS:
        print(f"--- Ratio {ratio*100:.1f}% ---")
        iter_cpcs = []
        for i in range(N_ITERATIONS):
            all_sampled_zones = []
            for cid in range(N_CLUSTERS):
                group_zones = list(gdf[gdf['cluster'] == cid]['SUBZONE_C'].values)
                num_to_sample = max(1, int(len(group_zones) * ratio))
                all_sampled_zones.extend(random.sample(group_zones, num_to_sample))
            
            subset_df = binned_df[binned_df['ORIGIN_SUBZONE'].isin(all_sampled_zones)]
            subset_law = subset_df.groupby('distance_bin')['P_bin_k_i'].mean().to_dict()
            
            all_pred = []
            for origin_zone in unique_origins:
                origin_zone_str = str(origin_zone)
                if origin_zone_str not in origin_spatial_cache: continue
                cache = origin_spatial_cache[origin_zone_str]
                p_bin_values = np.array([subset_law.get(float(b), 0.0) for b in cache['bins']])
                sum_az_values = np.array(cache['sum_az_list'])
                mask = (p_bin_values > 0) & (sum_az_values > 0)
                if not any(mask): continue
                
                t_hat_vals = cache['o_i'] * p_bin_values[mask] * (aj_values[mask] / sum_az_values[mask])
                all_pred.append(pd.DataFrame({
                    'ORIGIN_SUBZONE': origin_zone_str,
                    'DEST_SUBZONE': subzone_ids[mask],
                    'T_hat_ij': t_hat_vals
                }))
            
            if not all_pred:
                iter_cpcs.append(0)
                continue
                
            pred_df = pd.concat(all_pred)
            cpc = calculate_origin_averaged_cpc(real_trips, pred_df)
            iter_cpcs.append(cpc)
        
        avg_cpc = np.mean(iter_cpcs)
        print(f"📊 Ratio {ratio*100:.1f}% -> Avg Global CPC: {avg_cpc:.4f}")
        results_record.append({'Ratio': ratio, 'Avg_CPC': avg_cpc, 'Std_CPC': np.std(iter_cpcs)})

    # 4. Save and Plot
    results_df = pd.DataFrame(results_record)
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    plt.figure(figsize=(10, 6))
    plt.plot(results_df['Ratio'] * 100, results_df['Avg_CPC'], marker='o', color='r')
    plt.xscale('log')
    plt.xticks([1, 2, 5, 10, 20, 50, 100], [1, 2, 5, 10, 20, 50, 100])
    plt.xlabel('Sample Ratio (%)')
    plt.ylabel('Global CPC')
    plt.title('Singapore Mobility Law: Sensitivity Curve')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(CURRENT_DIR, 'step13_sensitivity_curve.png'))
    print(f"📈 Plot saved to {CURRENT_DIR}/step13_sensitivity_curve.png")

if __name__ == "__main__":
    main()
