import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
BINNED_FILE = 'binned_trips_by_zone.csv'
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
OUTPUT_FILE = 'step5_gravity_results.csv'
CITY_CRS = 'EPSG:5179'

def main():
    print("🚀 Step 5 (SEOUL Study): Modeling Version Global P_bin (Only P_bin)...")

    if not os.path.exists(BINNED_FILE) or not os.path.exists(SZ_SHAPEFILE):
        print(f"❌ Error: Required files missing.")
        return

    # 1. Load Data
    binned_df = pd.read_csv(BINNED_FILE)
    gdf = gpd.read_file(SZ_SHAPEFILE).to_crs(CITY_CRS)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(float)
    gdf['centroid'] = gdf.geometry.centroid
    
    unique_origins = binned_df['ORIGIN_SUBZONE'].unique()
    print(f"📊 Ready to process {len(unique_origins)} origin zones.")

    final_results = []

    # 2. Iterate using Global Probabilistic Logic
    for i, origin_zone in enumerate(unique_origins):
        if i % 100 == 0:
            print(f"📍 Progress: {i}/{len(unique_origins)}...")
            
        zone_binned = binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone].copy()
        o_i = zone_binned['COUNT'].sum()
        
        # P(bin_k) lookup
        total_p_trips = zone_binned['COUNT'].sum()
        zone_binned['P_bin_k'] = zone_binned['COUNT'] / total_p_trips
        p_bin_lookup = zone_binned.set_index('distance_bin')['P_bin_k'].to_dict()

        origin_feat = gdf[gdf['SUBZONE_C'] == origin_zone]
        if origin_feat.empty: continue
        origin_point = origin_feat.centroid.values[0]

        temp_gdf = gdf.copy()
        temp_gdf['d_ij_km'] = temp_gdf['centroid'].distance(origin_point) / 1000.0
        temp_gdf['bin_k'] = np.floor(temp_gdf['d_ij_km']).astype(float)
        
        # Denominator: Sum of P(bin_z) over ALL zones
        # This is equivalent to Sum_k (N_k * P_bin_k)
        bin_counts = temp_gdf.groupby('bin_k').size().to_dict()
        global_sum_p = sum(count * p_bin_lookup.get(k, 0.0) for k, count in bin_counts.items())

        # Apply Global Model: T_hat_ij = O_i * (P_bin_k / Global_Sum_P)
        for idx, row in temp_gdf.iterrows():
            bin_id = row['bin_k']
            p_bin_k = p_bin_lookup.get(bin_id, 0.0)
            
            if p_bin_k > 0 and global_sum_p > 0:
                t_hat_ij = o_i * (p_bin_k / global_sum_p)
                final_results.append({
                    'ORIGIN_ZONE': origin_zone,
                    'DEST_SUBZONE': row['SUBZONE_C'],
                    'bin_k': bin_id,
                    'T_hat_ij': t_hat_ij
                })

    # 3. Save Results
    results_df = pd.DataFrame(final_results)
    print(f"💾 Saving Step 5 results to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 5 Global Seoul Complete.")

if __name__ == "__main__":
    main()
