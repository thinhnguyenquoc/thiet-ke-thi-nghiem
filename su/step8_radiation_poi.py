import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
TRIPS_FILE = 'aggregated_trips.csv'
POI_FILE = 'pois_by_zone.csv'
OUTPUT_FILE = 'step8_radiation_results.csv'
PROJECTED_CRS = 'EPSG:5179'
EPSILON = 1.0

def main():
    print("🚀 Step 8 (SEOUL): Radiation POI Model (j != i Constraint)")

    # 1. Load Data
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.replace('.0', '', regex=False)
    gdf_utm = gdf.to_crs(PROJECTED_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    idx_to_zone = {i: z for i, z in enumerate(unique_zones)}
    centroids = gdf_utm.set_index('SUBZONE_C')['centroid'].to_dict()
    
    poi_df = pd.read_csv(POI_FILE)
    poi_df['SUBZONE_C'] = poi_df['SUBZONE_C'].astype(str).str.replace('.0', '', regex=False)
    poi_lookup = poi_df.set_index('SUBZONE_C')['A_j'].to_dict()
    gdf_utm['poi_m'] = gdf_utm['SUBZONE_C'].map(poi_lookup).fillna(0) + EPSILON
    zone_poi_dict = gdf_utm.set_index('SUBZONE_C')['poi_m'].to_dict()

    # 2. Load Trips and Handle Internal Flows
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    
    internal_lookup = trips_df[trips_df['ORIGIN_SUBZONE'] == trips_df['DESTINATION_SUBZONE']].set_index('ORIGIN_SUBZONE')['COUNT'].to_dict()
    external_trips = trips_df[trips_df['ORIGIN_SUBZONE'] != trips_df['DESTINATION_SUBZONE']]
    o_i_out_lookup = external_trips.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()

    # 3. Implement Radiation POI Model
    final_results = []
    
    for oz in unique_zones:
        # A. Ground Truth Internal Flow
        t_ii = internal_lookup.get(oz, 0.0)
        final_results.append({'ORIGIN_ZONE': oz, 'DEST_SUBZONE': oz, 'T_hat_ij': t_ii})

        # B. Predicted External Flows
        o_i_out = o_i_out_lookup.get(oz, 0.0)
        if o_i_out == 0: continue
        
        m_i = zone_poi_dict.get(oz, EPSILON)
        p_i = centroids[oz]
        
        temp_df = gdf_utm[gdf_utm['SUBZONE_C'] != oz].copy()
        temp_df['dist'] = temp_df['centroid'].distance(p_i)
        temp_df = temp_df.sort_values('dist')
        temp_df['s_ij'] = temp_df['poi_m'].shift(1).fillna(0).cumsum()
        
        n_j = temp_df['poi_m']
        s_ij = temp_df['s_ij']
        denom = (m_i + s_ij) * (m_i + n_j + s_ij)
        temp_df['T_hat_ij'] = np.where(denom > 0, o_i_out * (m_i * n_j) / denom, 0.0)
        
        for _, row in temp_df.iterrows():
            if row['T_hat_ij'] > 1e-4:
                final_results.append({
                    'ORIGIN_ZONE': oz, 'DEST_SUBZONE': row['SUBZONE_C'], 'T_hat_ij': row['T_hat_ij']
                })

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 8 complete (Seoul). Internal flows preserved.")

if __name__ == "__main__":
    main()
