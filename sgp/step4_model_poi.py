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
    print("🚀 Step 4 (Singapore): Working on Attraction-Weighted (POI)")

    # 1. Load Geometries
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    unique_zones = gdf_utm.index.values
    zone_to_idx = {z: i for i, z in enumerate(unique_zones)}
    idx_to_zone = {i: z for i, z in enumerate(unique_zones)}
    
    # Pre-calculate distance matrix and bins
    coords = np.array([[p.x, p.y] for p in gdf_utm['centroid']])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    bin_mat = np.floor(dist_mat).astype(int)

    # 2. Load POI Attractions (B_j)
    print("🏪 Loading POI attractions...")
    poi_df = pd.read_csv(POI_FILE)
    poi_df['SUBZONE_C'] = poi_df['SUBZONE_C'].astype(str).str.strip().str.upper()
    # Attraction vector B_j + epsilon
    attr_map = poi_df.set_index('SUBZONE_C')['A_j'].to_dict()
    attr_vec = np.array([attr_map.get(z, 0.0) for z in unique_zones]) + EPSILON

    # 3. Load zone-specific probability distributions
    if not os.path.exists(PROB_FILE):
        print(f"❌ Error: {PROB_FILE} not found. Run Step 3 first.")
        return
    print(f"📊 Loading probability distributions from {PROB_FILE}...")
    probs_df = pd.read_csv(PROB_FILE)
    prob_lookup = probs_df.groupby('ORIGIN_SUBZONE').apply(lambda x: x.set_index('distance_bin')['prob'].to_dict()).to_dict()

    # 4. Load Origin Totals (O_i)
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    o_i_lookup = trips_df.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()

    # 5. Prediction
    print("⚛️ Generating predictions...")
    final_results = []
    
    for oz in unique_zones:
        o_idx = zone_to_idx[oz]
        o_i = o_i_lookup.get(oz, 0.0)
        if o_i == 0: continue
        
        o_probs = prob_lookup.get(oz, {})
        if not o_probs: continue
        
        o_bins = bin_mat[o_idx]
        
        # Calculate denominator for each bin: sum(B_z + eps) for z in bin_k
        # This is origin-specific because "zones in bin_k" depends on origin
        unique_bins = np.unique(o_bins)
        bin_attr_sums = {}
        for b in unique_bins:
            mask_b = (o_bins == b)
            bin_attr_sums[b] = attr_vec[mask_b].sum()

        for d_idx, bin_id in enumerate(o_bins):
            p_bin = o_probs.get(float(bin_id), 0.0)
            denom = bin_attr_sums.get(bin_id, 0)
            
            if p_bin > 0 and denom > 0:
                # Formula: T_ij = O_i * P(bin) * (B_j / sum(B_z))
                t_hat_ij = o_i * p_bin * (attr_vec[d_idx] / denom)
                if t_hat_ij > 1e-6:
                    final_results.append({
                        'ORIGIN_ZONE': oz,
                        'DEST_SUBZONE': idx_to_zone[d_idx],
                        'T_hat_ij': t_hat_ij
                    })

    results_df = pd.DataFrame(final_results)
    print(f"💾 Saving POI-Weighted results ({len(results_df)} OD pairs) to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    print("✅ Step 4 complete.")

if __name__ == "__main__":
    main()
