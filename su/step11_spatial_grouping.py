import pandas as pd
import geopandas as gpd
import numpy as np
import os
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BINNED_FILE = os.path.join(CURRENT_DIR, 'binned_trips_by_zone.csv')
SZ_SHAPEFILE = os.path.join(CURRENT_DIR, 'sub_zone/data_seoul_subzone.shp')
POI_FILE = os.path.join(CURRENT_DIR, 'pois_by_zone.csv')
TRIP_FILE = os.path.join(CURRENT_DIR, 'aggregated_trips.csv')
OUTPUT_FILE = os.path.join(CURRENT_DIR, 'step11_spatial_grouping_results.csv')
PLOT_FILE = os.path.join(CURRENT_DIR, 'step11_spatial_clusters.png')
CITY_CRS = 'EPSG:5179'
N_CLUSTERS = 10

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
    print(f"🚀 Step 11: Spatial Grouping Experiment (Seoul) - {N_CLUSTERS} Clusters...")

    # 1. Load Data
    binned_df = pd.read_csv(BINNED_FILE)
    poi_df = pd.read_csv(POI_FILE)
    gdf = gpd.read_file(SZ_SHAPEFILE).to_crs(CITY_CRS)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(float)
    
    # Calculate centroids
    gdf['centroid'] = gdf.geometry.centroid
    coords = np.array([[c.x, c.y] for c in gdf['centroid']])

    # 2. Perform Spatial Clustering (K-Means)
    print(f"📍 Clustering {len(gdf)} subzones into {N_CLUSTERS} spatial groups...")
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    gdf['cluster'] = kmeans.fit_predict(coords)

    # Visualization
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(column='cluster', categorical=True, legend=True, ax=ax, cmap='tab10', edgecolor='black', linewidth=0.3)
    plt.title(f'Seoul Subzones Divided into {N_CLUSTERS} Spatial Clusters')
    plt.savefig(PLOT_FILE)
    print(f"📈 Cluster map saved to {PLOT_FILE}")

    # 3. Preparation for Cross-Validation
    subzone_ids = gdf['SUBZONE_C'].values
    aj_values = gdf.merge(poi_df[['SUBZONE_C', 'A_j']], on='SUBZONE_C', how='left').fillna(0)['A_j'].values
    all_centroids = np.array([[c.x, c.y] for c in gdf['centroid']])
    unique_origins = binned_df['ORIGIN_SUBZONE'].unique()
    zone_to_idx = {z: i for i, z in enumerate(subzone_ids)}
    
    real_trips = pd.read_csv(TRIP_FILE)[['ORIGIN_SUBZONE', 'DESTINATION_SUBZONE', 'COUNT']]
    real_trips.rename(columns={'DESTINATION_SUBZONE': 'DEST_SUBZONE'}, inplace=True)
    
    binned_df['P_bin_k_i'] = binned_df.groupby('ORIGIN_SUBZONE')['COUNT'].transform(lambda x: x / x.sum())

    # Precompute spatial structures
    print("📏 Precomputing spatial bins for each origin...")
    origin_spatial_cache = {}
    for origin_zone in unique_origins:
        # Check if origin_zone exists in gdf
        if origin_zone not in zone_to_idx: continue
        origin_idx = zone_to_idx[origin_zone]
        origin_pos = all_centroids[origin_idx]
        dists = np.sqrt(np.sum((all_centroids - origin_pos)**2, axis=1)) / 1000.0
        bins = np.floor(dists).astype(int)
        
        local_df = pd.DataFrame({'bin_k': bins, 'A_j': aj_values})
        bin_sums = local_df.groupby('bin_k')['A_j'].sum().to_dict()
        
        origin_spatial_cache[origin_zone] = {
            'bins': bins,
            'sum_az_list': [bin_sums[b] for b in bins],
            'o_i': binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone]['COUNT'].sum()
        }

    # 4. Leave-One-Cluster-Out Cross-Validation
    results = []
    print("🧪 Starting Leave-One-Cluster-Out Cross-Validation...")
    
    for cluster_id in range(N_CLUSTERS):
        print(f"--- Fold {cluster_id + 1}/{N_CLUSTERS} (Testing on Cluster {cluster_id}) ---")
        
        test_zones = gdf[gdf['cluster'] == cluster_id]['SUBZONE_C'].values
        train_zones = gdf[gdf['cluster'] != cluster_id]['SUBZONE_C'].values
        
        # Calculate Global Law from training zones
        train_df = binned_df[binned_df['ORIGIN_SUBZONE'].isin(train_zones)]
        avg_law = train_df.groupby('distance_bin')['P_bin_k_i'].mean().to_dict()
        
        # Predict for TEST zones
        all_pred = []
        for origin_zone in test_zones:
            if origin_zone not in origin_spatial_cache: continue
            cache = origin_spatial_cache[origin_zone]
            p_bin_values = np.array([avg_law.get(float(b), 0.0) for b in cache['bins']])
            sum_az_values = np.array(cache['sum_az_list'])
            mask = (p_bin_values > 0) & (sum_az_values > 0)
            if not any(mask): continue
            
            t_hat_vals = cache['o_i'] * p_bin_values[mask] * (aj_values[mask] / sum_az_values[mask])
            all_pred.append(pd.DataFrame({
                'ORIGIN_SUBZONE': origin_zone,
                'DEST_SUBZONE': subzone_ids[mask],
                'T_hat_ij': t_hat_vals
            }))
            
        if not all_pred:
            print(f"Warning: No predictions for cluster {cluster_id}")
            results.append({'Cluster': cluster_id, 'CPC': 0.0, 'Subzones': len(test_zones)})
            continue
            
        pred_df = pd.concat(all_pred)
        real_test_trips = real_trips[real_trips['ORIGIN_SUBZONE'].isin(test_zones)]
        
        cpc = calculate_origin_averaged_cpc(real_test_trips, pred_df)
        print(f"✅ Cluster {cluster_id} -> Avg CPC: {cpc:.4f} ({len(test_zones)} subzones)")
        results.append({'Cluster': cluster_id, 'CPC': cpc, 'Subzones': len(test_zones)})

    # Summary
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n📊 Summary Results saved to {OUTPUT_FILE}")
    print(f"Global Cross-Validated CPC: {results_df['CPC'].mean():.4f}")

if __name__ == "__main__":
    main()
