import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
POI_FILE = '../test-probability-distribution/detail_pois.geojson'
TRIPS_FILE = '../test-probability-distribution/data_trip_sum.csv'
BINNED_FILE = 'binned_trips_by_zone.csv'
OUTPUT_FILE = 'step4_gravity_results.csv'

def main():
    print("🚀 Step 4 (Global Scale): Version POI for ALL zones")

    # Load data
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    
    binned_df = pd.read_csv(BINNED_FILE)
    binned_df['ORIGIN_SUBZONE'] = binned_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    
    all_origin_zones = binned_df['ORIGIN_SUBZONE'].unique()
    print(f"📊 Detected {len(all_origin_zones)} origin zones.")

    gdf = gpd.read_file(POI_FILE)
    poi_cols = ['amenity', 'leisure', 'office', 'public_transport', 'shop', 'tourism']
    available_poi_cols = [c for c in poi_cols if c in gdf.columns]
    gdf['A_j'] = gdf[available_poi_cols].sum(axis=1)
    
    gdf_meter = gdf.to_crs(epsg=3414)
    gdf_meter['SUBZONE_C'] = gdf_meter['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_meter['centroid'] = gdf_meter.geometry.centroid

    final_results = []

    for i, origin_zone in enumerate(all_origin_zones):
        if i % 20 == 0:
            print(f"📍 Progress: {i}/{len(all_origin_zones)} zones processed...")
        
        o_i = trips_df[trips_df['ORIGIN_SUBZONE'] == origin_zone]['COUNT'].sum()
        
        zone_binned = binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone].copy()
        if zone_binned.empty: continue
        
        total_hist = zone_binned['COUNT'].sum()
        zone_binned['P_bin_k'] = zone_binned['COUNT'] / total_hist
        p_bin_lookup = zone_binned.set_index('distance_bin')['P_bin_k'].to_dict()

        origin_feat = gdf_meter[gdf_meter['SUBZONE_C'] == origin_zone]
        if origin_feat.empty: continue
        origin_point = origin_feat.centroid.values[0]

        # Vectors for distance and attraction weighting
        distances_km = gdf_meter.centroid.distance(origin_point).values / 1000.0
        bins_k = np.floor(distances_km).astype(float)
        
        # Temp df for attraction aggregation
        temp_agg = pd.DataFrame({'bin_k': bins_k, 'A_j': gdf_meter['A_j'].values})
        bin_attraction = temp_agg.groupby('bin_k')['A_j'].sum().to_dict()

        for idx, row in gdf_meter.iterrows():
            bin_id = bins_k[idx]
            p_bin = p_bin_lookup.get(bin_id, 0.0)
            aj = row['A_j']
            sum_az = bin_attraction.get(bin_id, 0.0)
            
            if p_bin > 0:
                t_hat_ij = o_i * p_bin * (aj / sum_az) if sum_az > 0 else 0.0
                final_results.append({
                    'ORIGIN_ZONE': origin_zone,
                    'DEST_SUBZONE': row['SUBZONE_C'],
                    'T_hat_ij': t_hat_ij
                })

    results_df = pd.DataFrame(final_results)
    print(f"💾 Saving global POI results ({len(results_df)} OD pairs) to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    print("✅ Step 4 Global complete.")

if __name__ == "__main__":
    main()
