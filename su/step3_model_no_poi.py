import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
BINNED_FILE = 'binned_trips_by_zone.csv'
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
OUTPUT_FILE = 'step3_gravity_results.csv'
CITY_CRS = 'EPSG:5179'  # Matching UTM-K used in Step 1

def main():
    print("🚀 Step 3 (SEOUL Study): Modeling Version No POI (Equal Distribution)...")

    if not os.path.exists(BINNED_FILE) or not os.path.exists(SZ_SHAPEFILE):
        print(f"❌ Error: Required files ({BINNED_FILE} or {SZ_SHAPEFILE}) missing.")
        return

    # 1. Load Data
    print("📖 Loading binned histograms and subzone geometries...")
    binned_df = pd.read_csv(BINNED_FILE)
    
    # We also need the shapefile to know which subzones exist and where they are
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf = gdf.to_crs(CITY_CRS)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(float) # Matching numeric IDs in binned data
    gdf['centroid'] = gdf.geometry.centroid
    
    unique_origins = binned_df['ORIGIN_SUBZONE'].unique()
    print(f"📊 Ready to process {len(unique_origins)} origin zones.")

    final_results = []

    # 2. Iterate through each origin zone
    for i, origin_zone in enumerate(unique_origins):
        if i % 50 == 0:
            print(f"📍 Progress: {i}/{len(unique_origins)} zones processed...")
            
        # O_i: Total trips production for this origin
        zone_binned = binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone].copy()
        o_i = zone_binned['COUNT'].sum()
        
        # P(bin_k): Probability lookup
        total_p_trips = zone_binned['COUNT'].sum()
        zone_binned['P_bin_k'] = zone_binned['COUNT'] / total_p_trips
        p_bin_lookup = zone_binned.set_index('distance_bin')['P_bin_k'].to_dict()

        # Origin point and distance to all other zones
        origin_feat = gdf[gdf['SUBZONE_C'] == origin_zone]
        if origin_feat.empty: continue
        origin_point = origin_feat.centroid.values[0]

        temp_gdf = gdf.copy()
        temp_gdf['d_ij_km'] = temp_gdf['centroid'].distance(origin_point) / 1000.0
        temp_gdf['bin_k'] = np.floor(temp_gdf['d_ij_km']).astype(float)
        
        # N_k: Number of subzones in each bin
        bin_counts = temp_gdf.groupby('bin_k').size().to_dict()

        # Apply Model: T_hat_ij = O_i * (P_bin_k / N_k)
        # Note: We only predict for bins that exist in the histogram
        for idx, row in temp_gdf.iterrows():
            bin_id = row['bin_k']
            p_bin_k = p_bin_lookup.get(bin_id, 0.0)
            n_k = bin_counts.get(bin_id, 0)
            
            if p_bin_k > 0:
                t_hat_ij = o_i * (p_bin_k / n_k)
                final_results.append({
                    'ORIGIN_ZONE': origin_zone,
                    'DEST_SUBZONE': row['SUBZONE_C'],
                    'bin_k': bin_id,
                    'T_hat_ij': t_hat_ij
                })

    # 3. Save Results
    results_df = pd.DataFrame(final_results)
    print(f"💾 Saving Step 3 results to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    total_predicted = results_df['T_hat_ij'].sum()
    print(f"✅ Step 3 Global Seoul Complete. Total Predicted Volume: {total_predicted:,.2f}")

if __name__ == "__main__":
    main()
