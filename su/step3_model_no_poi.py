import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
TRIPS_FILE = 'aggregated_trips.csv'
BINNED_FILE = 'binned_trips_by_zone.csv'
OUTPUT_FILE = 'step3_gravity_results.csv'
CITY_CRS = 'EPSG:5179'

def main():
    print("🚀 Step 3 (SEOUL): Attraction-Uniform (No POI) - j != i Constraint")

    # 1. Load Geometry
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.replace('.0', '', regex=False)
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    zone_to_idx = {z: i for i, z in enumerate(unique_zones)}
    idx_to_zone = {i: z for i, z in enumerate(unique_zones)}
    
    coords = np.array([[p.x, p.y] for p in gdf_utm['centroid']])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    bin_mat = np.floor(dist_mat).astype(int)

    # 2. Load Trips and Handle Internal Flows
    print("📖 Loading trips...")
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    
    internal_lookup = trips_df[trips_df['ORIGIN_SUBZONE'] == trips_df['DESTINATION_SUBZONE']].set_index('ORIGIN_SUBZONE')['COUNT'].to_dict()
    external_trips = trips_df[trips_df['ORIGIN_SUBZONE'] != trips_df['DESTINATION_SUBZONE']]
    o_i_out_lookup = external_trips.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()

    # 3. Load inter-zone probability distributions
    print("🧮 Loading empirical inter-zone probability distributions...")
    binned_df = pd.read_csv(BINNED_FILE)
    binned_df['ORIGIN_SUBZONE'] = binned_df['ORIGIN_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    
    probs_list = []
    for origin_zone in binned_df['ORIGIN_SUBZONE'].unique():
        zone_data = binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone].copy()
        total_count = zone_data['COUNT'].sum()
        if total_count > 0:
            zone_data['prob'] = zone_data['COUNT'] / total_count
            probs_list.append(zone_data[['ORIGIN_SUBZONE', 'distance_bin', 'prob']])
            
    probs_df = pd.concat(probs_list)
    prob_lookup = probs_df.groupby('ORIGIN_SUBZONE').apply(lambda x: x.set_index('distance_bin')['prob'].to_dict()).to_dict()

    # 4. Prediction
    final_results = []
    for oz in unique_zones:
        # A. Ground Truth Internal Flow
        t_ii = internal_lookup.get(oz, 0.0)
        final_results.append({'ORIGIN_ZONE': oz, 'DEST_SUBZONE': oz, 'T_hat_ij': t_ii})

        # B. Predict External Flows
        o_i_out = o_i_out_lookup.get(oz, 0.0)
        if o_i_out == 0: continue
        
        o_probs = prob_lookup.get(oz, {})
        o_idx = zone_to_idx[oz]
        o_bins = bin_mat[o_idx]
        
        # Count external zones per bin
        mask_ext = (unique_zones != oz)
        ext_bins = o_bins[mask_ext]
        ubins, counts = np.unique(ext_bins, return_counts=True)
        bin_counts_ext = dict(zip(ubins, counts))

        for d_idx, bin_id in enumerate(o_bins):
            dz = idx_to_zone[d_idx]
            if dz == oz: continue
            
            p_bin = o_probs.get(float(bin_id), 0.0)
            n_k_ext = bin_counts_ext.get(bin_id, 0)
            
            if p_bin > 0 and n_k_ext > 0:
                t_hat_ij = o_i_out * (p_bin / n_k_ext)
                final_results.append({
                    'ORIGIN_ZONE': oz, 'DEST_SUBZONE': dz, 'T_hat_ij': t_hat_ij
                })

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 3 complete (Seoul). Internal flows preserved.")

if __name__ == "__main__":
    main()
