import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
TRIPS_FILE = 'data_trip_sum.csv'
BINNED_FILE = 'binned_trips_by_zone.csv'
PROB_FILE = 'prob_dist_by_zone.csv'
OUTPUT_FILE = 'step3_gravity_results.csv'
CITY_CRS = 'EPSG:3414'

def main():
    print("🚀 Step 3 (Singapore): Working on Attraction-Uniform (No POI)")

    # 1. Load Geometry and calculate distance matrix
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    zone_to_idx = {z: i for i, z in enumerate(unique_zones)}
    idx_to_zone = {i: z for i, z in enumerate(unique_zones)}
    
    # Calculate all-pairs distance matrix
    coords = np.array([[p.x, p.y] for p in gdf_utm['centroid']])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    bin_mat = np.floor(dist_mat).astype(int)

    # 2. Load trips and binned distribution
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    o_i_lookup = trips_df.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()
    
    binned_df = pd.read_csv(BINNED_FILE)
    binned_df['ORIGIN_SUBZONE'] = binned_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    
    # Calculate and Save P(bin_k | i)
    print("🧮 Calculating and saving zone-specific probability distributions...")
    probs_list = []
    all_origin_zones_in_binned = binned_df['ORIGIN_SUBZONE'].unique()
    
    for origin_zone in all_origin_zones_in_binned:
        zone_data = binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone].copy()
        total_count = zone_data['COUNT'].sum()
        if total_count > 0:
            zone_data['prob'] = zone_data['COUNT'] / total_count
            probs_list.append(zone_data[['ORIGIN_SUBZONE', 'distance_bin', 'prob']])
            
    probs_df = pd.concat(probs_list)
    probs_df.to_csv(PROB_FILE, index=False)
    print(f"📊 Saved probability distribution to {PROB_FILE}")

    # 3. prediction
    final_results = []
    
    # Create a nested lookup for efficiency: {origin: {bin: prob}}
    prob_lookup = probs_df.groupby('ORIGIN_SUBZONE').apply(lambda x: x.set_index('distance_bin')['prob'].to_dict()).to_dict()

    for origin_zone in unique_zones:
        o_idx = zone_to_idx[origin_zone]
        o_i = o_i_lookup.get(origin_zone, 0.0)
        if o_i == 0: continue
        
        o_probs = prob_lookup.get(origin_zone, {})
        if not o_probs: continue
        
        # Get zones per bin for this origin
        o_bins = bin_mat[o_idx]
        # Count occurrences of each bin ID in o_bins
        unique_bins, counts = np.unique(o_bins, return_counts=True)
        bin_counts = dict(zip(unique_bins, counts))

        for d_idx, bin_id in enumerate(o_bins):
            # Same zone (bin 0) is often omitted or handled normally
            p_bin = o_probs.get(float(bin_id), 0.0)
            n_k = bin_counts.get(bin_id, 0)
            
            if p_bin > 0 and n_k > 0:
                t_hat_ij = o_i * (p_bin / n_k)
                final_results.append({
                    'ORIGIN_ZONE': origin_zone,
                    'DEST_SUBZONE': idx_to_zone[d_idx],
                    'T_hat_ij': t_hat_ij
                })

    results_df = pd.DataFrame(final_results)
    print(f"💾 Saving results ({len(results_df)} OD pairs) to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    print("✅ Step 3 complete.")

if __name__ == "__main__":
    main()
