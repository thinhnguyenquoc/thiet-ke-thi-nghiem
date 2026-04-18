import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
TRIPS_FILE = 'data_trip_sum.csv'
POI_FILE = 'pois_by_zone.csv'
PROB_FILE = 'prob_dist_by_zone.csv'
OUTPUT_FILE = 'step4_gravity_results.csv'
CITY_CRS = 'EPSG:3414'
EPSILON = 1.0

def main():
    print("🚀 Step 4 (Singapore): Attraction-Weighted (POI) - j != i Constraint")

    # 1. Load Geometries
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    unique_zones = gdf_utm.index.values
    zone_to_idx = {z: i for i, z in enumerate(unique_zones)}
    idx_to_zone = {i: z for i, z in enumerate(unique_zones)}
    
    coords = np.array([[p.x, p.y] for p in gdf_utm['centroid']])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    bin_mat = np.floor(dist_mat).astype(int)

    # 2. Load POI Attractions (B_j)
    poi_df = pd.read_csv(POI_FILE)
    poi_df['SUBZONE_C'] = poi_df['SUBZONE_C'].astype(str).str.strip().str.upper()
    attr_map = poi_df.set_index('SUBZONE_C')['A_j'].to_dict()
    attr_vec = np.array([attr_map.get(z, 0.0) for z in unique_zones]) + EPSILON

    # 3. Load Trips and Handle Internal Flows
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(str).str.strip().str.upper()
    
    internal_lookup = trips_df[trips_df['ORIGIN_SUBZONE'] == trips_df['DESTINATION_SUBZONE']].set_index('ORIGIN_SUBZONE')['COUNT'].to_dict()
    external_trips = trips_df[trips_df['ORIGIN_SUBZONE'] != trips_df['DESTINATION_SUBZONE']]
    o_i_out_lookup = external_trips.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()

    # 4. Load inter-zone probability distributions (from Step 3/Step 1 update)
    if not os.path.exists(PROB_FILE):
        print(f"❌ Error: {PROB_FILE} not found. Run Step 1 & 3 first.")
        return
    probs_df = pd.read_csv(PROB_FILE)
    prob_lookup = probs_df.groupby('ORIGIN_SUBZONE').apply(lambda x: x.set_index('distance_bin')['prob'].to_dict()).to_dict()

    # 5. Prediction
    final_results = []
    
    for oz in unique_zones:
        # A. Ground Truth Internal Flow
        t_ii = internal_lookup.get(oz, 0.0)
        final_results.append({
            'ORIGIN_ZONE': oz, 'DEST_SUBZONE': oz, 'T_hat_ij': t_ii
        })

        # B. Predicted External Flows
        o_i_out = o_i_out_lookup.get(oz, 0.0)
        if o_i_out == 0: continue
        
        o_probs = prob_lookup.get(oz, {})
        o_idx = zone_to_idx[oz]
        o_bins = bin_mat[o_idx]
        
        # Denominator per bin (excluding origin oz from denominator)
        unique_bins = np.unique(o_bins)
        bin_attr_sums_ext = {}
        for b in unique_bins:
            mask_b_ext = (o_bins == b) & (unique_zones != oz)
            bin_attr_sums_ext[b] = attr_vec[mask_b_ext].sum()

        for d_idx, bin_id in enumerate(o_bins):
            dz = idx_to_zone[d_idx]
            if dz == oz: continue
            
            p_bin = o_probs.get(float(bin_id), 0.0)
            denom_ext = bin_attr_sums_ext.get(bin_id, 0)
            
            if p_bin > 0 and denom_ext > 0:
                t_hat_ij = o_i_out * p_bin * (attr_vec[d_idx] / denom_ext)
                if t_hat_ij > 1e-6:
                    final_results.append({
                        'ORIGIN_ZONE': oz, 'DEST_SUBZONE': dz, 'T_hat_ij': t_hat_ij
                    })

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 4 complete. POI weights applied for inter-zone flows only.")

if __name__ == "__main__":
    main()
