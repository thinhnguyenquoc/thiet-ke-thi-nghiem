import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
TRIPS_FILE = 'data_trip_sum.csv'
POI_SUMMARY_FILE = 'pois_by_zone.csv'
OUTPUT_FILE = 'step8_radiation_results.csv'
CITY_CRS = 'EPSG:3414'
EPSILON = 1.0

def main():
    print("🚀 Step 8 (SINGAPORE): Radiation POI Model (j != i Constraint)")

    # 1. Load Data
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    centroids_utm = gdf_utm.set_index('SUBZONE_C')['centroid'].to_dict()
    
    poi_df = pd.read_csv(POI_SUMMARY_FILE)
    poi_df['SUBZONE_C'] = poi_df['SUBZONE_C'].astype(str).str.strip().str.upper()
    poi_lookup = poi_df.set_index('SUBZONE_C')['A_j'].to_dict()
    gdf_utm['poi_m'] = gdf_utm['SUBZONE_C'].map(poi_lookup).fillna(0) + EPSILON
    
    # 2. Load Trips and Handle Internal Flows
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(str).str.strip().str.upper()
    
    internal_lookup = trips_df[trips_df['ORIGIN_SUBZONE'] == trips_df['DESTINATION_SUBZONE']].set_index('ORIGIN_SUBZONE')['COUNT'].to_dict()
    external_trips = trips_df[trips_df['ORIGIN_SUBZONE'] != trips_df['DESTINATION_SUBZONE']]
    o_i_out_lookup = external_trips.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()

    # 3. Implement Radiation POI Model for j != i
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    zone_poi_dict = gdf_utm.set_index('SUBZONE_C')['poi_m'].to_dict()
    
    final_results = []
    
    for i_zone in unique_zones:
        # A. Ground Truth Internal Flow
        t_ii = internal_lookup.get(i_zone, 0.0)
        final_results.append({'ORIGIN_ZONE': i_zone, 'DEST_SUBZONE': i_zone, 'T_hat_ij': t_ii})

        # B. Predicted External Flows
        o_i_out = o_i_out_lookup.get(i_zone, 0.0)
        if o_i_out == 0: continue
        
        m_i = zone_poi_dict.get(i_zone, EPSILON)
        p_i = centroids_utm[i_zone]
        
        temp_df = gdf_utm[gdf_utm['SUBZONE_C'] != i_zone].copy()
        temp_df['dist'] = temp_df['centroid'].distance(p_i)
        temp_df = temp_df.sort_values('dist')
        temp_df['s_ij'] = temp_df['poi_m'].shift(1).fillna(0).cumsum()
        
        n_j = temp_df['poi_m']
        s_ij = temp_df['s_ij']
        denom = (m_i + s_ij) * (m_i + n_j + s_ij)
        temp_df['T_hat_ij'] = np.where(denom > 0, o_i_out * (m_i * n_j) / denom, 0.0)
        
        for _, row in temp_df.iterrows():
            if row['T_hat_ij'] > 1e-6:
                final_results.append({
                    'ORIGIN_ZONE': i_zone, 'DEST_SUBZONE': row['SUBZONE_C'], 'T_hat_ij': row['T_hat_ij']
                })

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 8 complete. Internal flows preserved as ground truth.")

if __name__ == "__main__":
    main()
