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
    print("🚀 Step 3 (Singapore): Working on Attraction-Uniform (No POI) - j != i Constraint")

    # 1. Load Geometry and calculate distance matrix
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    zone_to_idx = {z: i for i, z in enumerate(unique_zones)}
    idx_to_zone = {i: z for i, z in enumerate(unique_zones)}
    
    coords = np.array([[p.x, p.y] for p in gdf_utm['centroid']])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    bin_mat = np.floor(dist_mat).astype(int)

    # 2. Load trips
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(str).str.strip().str.upper()
    
    # Store internal flows as Ground Truth
    internal_flows = trips_df[trips_df['ORIGIN_SUBZONE'] == trips_df['DESTINATION_SUBZONE']]
    internal_lookup = internal_flows.set_index('ORIGIN_SUBZONE')['COUNT'].to_dict()

    # Calculate Total Outflows (O_i^out) for j != i
    external_trips = trips_df[trips_df['ORIGIN_SUBZONE'] != trips_df['DESTINATION_SUBZONE']]
    o_i_out_lookup = external_trips.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()
    
    # Probability distribution P(bin_k | i) - Should come from processed inter-zone bins
    binned_df = pd.read_csv(BINNED_FILE) 
    binned_df['ORIGIN_SUBZONE'] = binned_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    
    print("🧮 Calculating inter-zone probability distributions...")
    probs_list = []
    for origin_zone in binned_df['ORIGIN_SUBZONE'].unique():
        zone_data = binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone].copy()
        total_count = zone_data['COUNT'].sum()
        if total_count > 0:
            zone_data['prob'] = zone_data['COUNT'] / total_count
            probs_list.append(zone_data[['ORIGIN_SUBZONE', 'distance_bin', 'prob']])
            
    probs_df = pd.concat(probs_list)
    probs_df.to_csv(PROB_FILE, index=False)
    prob_lookup = probs_df.groupby('ORIGIN_SUBZONE').apply(lambda x: x.set_index('distance_bin')['prob'].to_dict()).to_dict()

    # 3. Prediction
    final_results = []
    
    for origin_zone in unique_zones:
        # A. Handle Internal Flow (Ground Truth)
        t_ii = internal_lookup.get(origin_zone, 0.0)
        final_results.append({
            'ORIGIN_ZONE': origin_zone,
            'DEST_SUBZONE': origin_zone,
            'T_hat_ij': t_ii
        })

        # B. Predict External Flows (j != i)
        o_i_out = o_i_out_lookup.get(origin_zone, 0.0)
        if o_i_out == 0: continue
        
        o_probs = prob_lookup.get(origin_zone, {})
        o_idx = zone_to_idx[origin_zone]
        
        # Count external zones per bin for this origin
        o_bins = bin_mat[o_idx]
        mask_external = unique_zones != origin_zone
        
        # We need the count of j != i in each bin
        external_zones_bins = o_bins[mask_external]
        unique_bins, counts = np.unique(external_zones_bins, return_counts=True)
        bin_counts_ext = dict(zip(unique_bins, counts))

        for d_idx, bin_id in enumerate(o_bins):
            dest_zone = idx_to_zone[d_idx]
            if dest_zone == origin_zone: continue # Handled above
            
            p_bin = o_probs.get(float(bin_id), 0.0)
            n_k_ext = bin_counts_ext.get(bin_id, 0)
            
            if p_bin > 0 and n_k_ext > 0:
                t_hat_ij = o_i_out * (p_bin / n_k_ext) # Uniform allocation among external zones in bin
                final_results.append({
                    'ORIGIN_ZONE': origin_zone,
                    'DEST_SUBZONE': dest_zone,
                    'T_hat_ij': t_hat_ij
                })

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 3 complete. Internal flows preserved as ground truth.")

if __name__ == "__main__":
    main()
