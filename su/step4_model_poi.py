import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
BINNED_FILE = 'binned_trips_by_zone.csv'
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
POI_FILE = 'pois_by_zone.csv'
OUTPUT_FILE = 'step4_gravity_results.csv'
CITY_CRS = 'EPSG:5179'

def main():
    print("🚀 Step 4 (SEOUL Study): Modeling Version POI (using OSMNX Attraction A_j)...")

    if not all(os.path.exists(f) for f in [BINNED_FILE, SZ_SHAPEFILE, POI_FILE]):
        print(f"❌ Error: Required data missing ({BINNED_FILE}, {SZ_SHAPEFILE}, or {POI_FILE}).")
        return

    # 1. Load Data
    print("📖 Loading trips, geometries, and POI attraction data...")
    binned_df = pd.read_csv(BINNED_FILE)
    poi_df = pd.read_csv(POI_FILE)
    gdf = gpd.read_file(SZ_SHAPEFILE).to_crs(CITY_CRS)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(float)
    
    # Merge POI Attraction into geometry gdf
    # pois_by_zone.csv has 'SUBZONE_C' and 'A_j'
    gdf = gdf.merge(poi_df[['SUBZONE_C', 'A_j']], on='SUBZONE_C', how='left').fillna(0)
    gdf['centroid'] = gdf.geometry.centroid
    
    unique_origins = binned_df['ORIGIN_SUBZONE'].unique()
    print(f"📊 Ready to process {len(unique_origins)} origin zones.")

    final_results = []

    # 2. Iterate and model using POI weights
    for i, origin_zone in enumerate(unique_origins):
        if i % 100 == 0:
            print(f"📍 Progress: {i}/{len(unique_origins)} zones processed...")
            
        zone_binned = binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone].copy()
        o_i = zone_binned['COUNT'].sum()
        
        total_p_trips = zone_binned['COUNT'].sum()
        zone_binned['P_bin_k'] = zone_binned['COUNT'] / total_p_trips
        p_bin_lookup = zone_binned.set_index('distance_bin')['P_bin_k'].to_dict()

        origin_feat = gdf[gdf['SUBZONE_C'] == origin_zone]
        if origin_feat.empty: continue
        origin_point = origin_feat.centroid.values[0]

        temp_gdf = gdf.copy()
        temp_gdf['d_ij_km'] = temp_gdf['centroid'].distance(origin_point) / 1000.0
        temp_gdf['bin_k'] = np.floor(temp_gdf['d_ij_km']).astype(float)
        
        # S_k: Sum of Attraction A_j per bin
        bin_attraction_sum = temp_gdf.groupby('bin_k')['A_j'].sum().to_dict()

        for idx, row in temp_gdf.iterrows():
            bin_id = row['bin_k']
            p_bin_k = p_bin_lookup.get(bin_id, 0.0)
            aj = row['A_j']
            sum_az = bin_attraction_sum.get(bin_id, 0.0)
            
            if p_bin_k > 0 and sum_az > 0:
                t_hat_ij = o_i * p_bin_k * (aj / sum_az)
                final_results.append({
                    'ORIGIN_ZONE': origin_zone,
                    'DEST_SUBZONE': row['SUBZONE_C'],
                    'bin_k': bin_id,
                    'T_hat_ij': t_hat_ij
                })

    # 3. Save Results
    results_df = pd.DataFrame(final_results)
    print(f"💾 Saving Step 4 results to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 4 Complete using real Seoul POIs.")

if __name__ == "__main__":
    main()
