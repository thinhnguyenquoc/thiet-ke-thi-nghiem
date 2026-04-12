import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
TRIPS_FILE = 'aggregated_trips.csv'
POI_FILE = 'pois_by_zone.csv'
OUTPUT_FILE = 'step8_radiation_results.csv'
CITY_CRS = 'EPSG:5179' # UTM-K for Seoul

def calculate_cpc(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    if total == 0: return 0
    return 2 * intersection / total

def main():
    print("🚀 Step 9 (SEOUL): Radiation POI Model Implementation...")

    # 1. Load Geometries
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str)
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    centroids_utm = gdf_utm.set_index('SUBZONE_C')['centroid'].to_dict()
    
    # 2. Load POI counts as mass
    poi_df = pd.read_csv(POI_FILE)
    poi_df['SUBZONE_C'] = poi_df['SUBZONE_C'].astype(str)
    poi_lookup = poi_df.set_index('SUBZONE_C')['A_j'].to_dict()
    
    gdf_utm['poi_m'] = gdf_utm['SUBZONE_C'].map(poi_lookup).fillna(1.0) # Ensure at least 1 POI for formula stability
    print(f"📈 Total POIs mapped to zones: {gdf_utm['poi_m'].sum():,.0f}")
    
    # 3. Load Empirical Trips for T_i
    trips_df = pd.read_csv(TRIPS_FILE)
    # IDs appear to be floats like 1119054.0, convert to int then str
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(float).astype(int).astype(str)
    t_i_lookup = trips_df.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()
    
    # 4. Implement Radiation POI Model
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    zone_poi_dict = gdf_utm.set_index('SUBZONE_C')['poi_m'].to_dict()
    
    final_results = []
    
    for count, i_zone in enumerate(unique_zones):
        if count % 100 == 0:
            print(f"📍 Processed {count}/{len(unique_zones)} origin zones...")
            
        t_i = t_i_lookup.get(i_zone, 0.0)
        if t_i == 0: continue
        
        m_i = zone_poi_dict.get(i_zone, 1.0)
        p_i = centroids_utm[i_zone]
        
        temp_df = gdf_utm[gdf_utm['SUBZONE_C'] != i_zone].copy()
        temp_df['dist'] = temp_df['centroid'].distance(p_i)
        
        # Sort and cumulative sum for s_ij (POI intervening opportunities)
        temp_df = temp_df.sort_values('dist')
        temp_df['s_ij'] = temp_df['poi_m'].shift(1).fillna(0).cumsum()
        
        # Radiation formula with POIs
        denom = (m_i + temp_df['s_ij']) * (m_i + temp_df['poi_m'] + temp_df['s_ij'])
        temp_df['T_hat_ij'] = np.where(denom > 0, t_i * (m_i * temp_df['poi_m']) / denom, 0.0)
        
        for _, row in temp_df.iterrows():
            if row['T_hat_ij'] > 0:
                final_results.append({
                    'ORIGIN_ZONE': i_zone,
                    'DEST_SUBZONE': row['SUBZONE_C'],
                    'T_hat_ij': row['T_hat_ij']
                })

    # 5. Save Results
    if not final_results:
        results_df = pd.DataFrame(columns=['ORIGIN_ZONE', 'DEST_SUBZONE', 'T_hat_ij'])
    else:
        results_df = pd.DataFrame(final_results)
    
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    if 'T_hat_ij' in results_df.columns:
        total_predicted = results_df['T_hat_ij'].sum()
        print(f"✅ Step 9 Radiation POI Complete. Total Predicted Volume: {total_predicted:,.2f}")
    else:
        print("⚠️ Warning: No trips predicted.")

if __name__ == "__main__":
    main()
