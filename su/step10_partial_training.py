import pandas as pd
import geopandas as gpd
import numpy as np
import os
import random
import matplotlib.pyplot as plt

# Configuration
BINNED_FILE = 'binned_trips_by_zone.csv'
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
POI_FILE = 'pois_by_zone.csv'
TRIP_FILE = 'aggregated_trips.csv'
OUTPUT_FILE = 'step10_partial_training_results.csv'
PLOT_FILE = 'step10_cpc_growth_curve.png'
CITY_CRS = 'EPSG:5179'

def calculate_origin_averaged_cpc(real_df, pred_df):
    unique_origins = real_df['ORIGIN_SUBZONE'].unique()
    cpcs = []
    real_gb = real_df.groupby('ORIGIN_SUBZONE')
    pred_gb = pred_df.groupby('ORIGIN_SUBZONE')
    for origin in unique_origins:
        if origin not in pred_gb.groups:
            cpcs.append(0.0)
            continue
        r_z = real_gb.get_group(origin)[['DEST_SUBZONE', 'COUNT']]
        p_z = pred_gb.get_group(origin)[['DEST_SUBZONE', 'T_hat_ij']]
        merged = pd.merge(r_z, p_z, on='DEST_SUBZONE', how='outer').fillna(0)
        y_true = merged['COUNT'].values
        y_pred = merged['T_hat_ij'].values
        intersection = np.sum(np.minimum(y_true, y_pred))
        total = np.sum(y_true) + np.sum(y_pred)
        cpcs.append(2.0 * intersection / total if total > 0 else 0.0)
    return np.mean(cpcs)

def main():
    print("🚀 Step 10: Expanded Partial-Training Shell Analysis (Seoul)...")

    # 1. Load Data
    binned_df = pd.read_csv(BINNED_FILE)
    poi_df = pd.read_csv(POI_FILE)
    gdf = gpd.read_file(SZ_SHAPEFILE).to_crs(CITY_CRS)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(float)
    gdf = gdf.merge(poi_df[['SUBZONE_C', 'A_j']], on='SUBZONE_C', how='left').fillna(0)
    gdf['centroid'] = gdf.geometry.centroid
    
    unique_origins = binned_df['ORIGIN_SUBZONE'].unique()
    zone_to_idx = {z: i for i, z in enumerate(unique_origins)}
    subzone_ids = gdf['SUBZONE_C'].values
    aj_values = gdf['A_j'].values
    all_centroids = np.array([[c.x, c.y] for c in gdf['centroid']])

    real_trips = pd.read_csv(TRIP_FILE)[['ORIGIN_SUBZONE', 'DESTINATION_SUBZONE', 'COUNT']]
    real_trips.rename(columns={'DESTINATION_SUBZONE': 'DEST_SUBZONE'}, inplace=True)

    # 2. Precompute Origin-specific Structures
    # Pre-calculating bin membership and sum_az for each origin
    print("📏 Precomputing spatial bins and attraction sums for each origin...")
    origin_spatial_cache = {}
    for origin_zone in unique_origins:
        origin_idx = zone_to_idx[origin_zone]
        origin_pos = all_centroids[origin_idx]
        dists = np.sqrt(np.sum((all_centroids - origin_pos)**2, axis=1)) / 1000.0
        bins = np.floor(dists).astype(int)
        
        # Calculate sum of attraction per bin for this origin
        local_df = pd.DataFrame({'bin_k': bins, 'A_j': aj_values})
        bin_sums = local_df.groupby('bin_k')['A_j'].sum().to_dict()
        
        origin_spatial_cache[origin_zone] = {
            'bins': bins,
            'sum_az_list': [bin_sums[b] for b in bins],
            'o_i': binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone]['COUNT'].sum()
        }

    # 3. Define Scenarios
    ratios = [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0]
    results_record = []

    binned_df['P_bin_k_i'] = binned_df.groupby('ORIGIN_SUBZONE')['COUNT'].transform(lambda x: x / x.sum())

    for ratio in ratios:
        print(f"🧪 Testing Ratio: {ratio*100}% Training Zones...")
        if ratio == 1.0:
            train_zones = unique_origins
        else:
            num_train = max(1, int(len(unique_origins) * ratio))
            train_zones = random.sample(list(unique_origins), num_train)
        
        train_df = binned_df[binned_df['ORIGIN_SUBZONE'].isin(train_zones)]
        avg_dist = train_df.groupby('distance_bin')['P_bin_k_i'].mean().to_dict()
        
        all_pred = []
        for i, origin_zone in enumerate(unique_origins):
            cache = origin_spatial_cache[origin_zone]
            p_bin_values = np.array([avg_dist.get(float(b), 0.0) for b in cache['bins']])
            sum_az_values = np.array(cache['sum_az_list'])
            mask = (p_bin_values > 0) & (sum_az_values > 0)
            if not any(mask): continue
            t_hat_vals = cache['o_i'] * p_bin_values[mask] * (aj_values[mask] / sum_az_values[mask])
            all_pred.append(pd.DataFrame({
                'ORIGIN_SUBZONE': origin_zone,
                'DEST_SUBZONE': subzone_ids[mask],
                'T_hat_ij': t_hat_vals
            }))
        
        pred_df = pd.concat(all_pred)
        cpc = calculate_origin_averaged_cpc(real_trips, pred_df)
        print(f"✅ Ratio {ratio*100}% -> Avg CPC: {cpc:.4f}")
        results_record.append({'Training_Ratio': ratio, 'CPC': cpc})

    # 4. Save and Plot
    results_df = pd.DataFrame(results_record)
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(results_df['Training_Ratio'] * 100, results_df['CPC'], marker='o', linestyle='-', color='b')
    plt.axhline(y=0.7623, color='r', linestyle='--', label='Full Training (0.7623)')
    plt.xlabel('Training Set Percentage (%)')
    plt.ylabel('CPC Score')
    plt.title('Seoul Mobility Law: CPC Growth vs. Training Data Ratio')
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    plt.legend()
    plt.savefig(PLOT_FILE)
    print(f"📈 Plot saved to {PLOT_FILE}")

if __name__ == "__main__":
    main()
