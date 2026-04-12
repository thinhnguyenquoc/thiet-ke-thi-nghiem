import pandas as pd
import geopandas as gpd
import numpy as np
import os
from PIL import Image
from shapely.geometry import Point

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
TRIPS_FILE = 'data_trip_sum.csv'
POP_TIF = 'sgp_pop_2025_CN_1km_R2025A_UA_v1.tif'
OUTPUT_FILE = 'step6_radiation_results.csv'
CITY_CRS = 'EPSG:3414' # SVY21 for Singapore

def main():
    print("🚀 Step 6 (SINGAPORE): Radiation Model Implementation...")

    # 1. Load Geometries
    print("📖 Loading subzone geometries...")
    gdf = gpd.read_file(SZ_SHAPEFILE)
    
    # Calculate centroids for distances (in SVY21 for accuracy)
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    centroids_utm = gdf_utm.set_index('SUBZONE_C')['centroid'].to_dict()
    
    # 2. Extract Population per Zone
    print("📊 Extracting population from TIFF...")
    with Image.open(POP_TIF) as img:
        pop_data = np.array(img).astype(float)
        tiepoint = img.tag[33922]
        pixel_scale = img.tag[33550]
        lon_orig, lat_orig = tiepoint[3], tiepoint[4]
        dx, dy = pixel_scale[0], pixel_scale[1]
        rows, cols = pop_data.shape
        c_cols, r_rows = np.meshgrid(np.arange(cols), np.arange(rows))
        lons = lon_orig + (c_cols + 0.5) * dx
        lats = lat_orig - (r_rows + 0.5) * dy
        mask = (pop_data > 0) & (~np.isnan(pop_data))
        valid_pop = pop_data[mask]
        valid_lons = lons[mask]
        valid_lats = lats[mask]
        
    print(f"✨ Found {len(valid_pop)} pixels with population data.")
    
    pixel_gdf = gpd.GeoDataFrame(
        {'pop': valid_pop}, 
        geometry=[Point(x, y) for x, y in zip(valid_lons, valid_lats)],
        crs="EPSG:4326"
    )
    
    # Zone geometries are in EPSG:4326
    print("📍 Spatial Join: Mapping pixels to subzones...")
    joined = gpd.sjoin(pixel_gdf, gdf[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
    zone_pop = joined.groupby('SUBZONE_C')['pop'].sum().to_dict()
    
    gdf_utm['pop_m'] = gdf_utm['SUBZONE_C'].map(zone_pop).fillna(0)
    print(f"📈 Total population mapped to zones: {gdf_utm['pop_m'].sum():,.0f}")
    
    # 3. Load Empirical Trips for T_i (Total departures)
    print("📖 Loading empirical trips...")
    trips_df = pd.read_csv(TRIPS_FILE)
    t_i_lookup = trips_df.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()
    
    # 4. Implement Radiation Model
    print("⚛️ Calculating Radiation Model predictions...")
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    zone_pop_dict = gdf_utm.set_index('SUBZONE_C')['pop_m'].to_dict()
    
    final_results = []
    
    for count, i_zone in enumerate(unique_zones):
        if count % 50 == 0:
            print(f"📍 Processed {count}/{len(unique_zones)} origin zones...")
            
        t_i = t_i_lookup.get(i_zone, 0.0)
        if t_i == 0: continue
        
        m_i = zone_pop_dict.get(i_zone, 0.0)
        p_i = centroids_utm[i_zone]
        
        # Calculate distances to all other zones
        temp_df = gdf_utm[gdf_utm['SUBZONE_C'] != i_zone].copy()
        temp_df['dist'] = temp_df['centroid'].distance(p_i)
        
        # Sort and cumulative sum for s_ij
        temp_df = temp_df.sort_values('dist')
        temp_df['s_ij'] = temp_df['pop_m'].shift(1).fillna(0).cumsum()
        
        # Radiation formula
        # T_ij = T_i * (m_i * n_j) / [(m_i + s_ij) * (m_i + n_j + s_ij)]
        denom = (m_i + temp_df['s_ij']) * (m_i + temp_df['pop_m'] + temp_df['s_ij'])
        temp_df['T_hat_ij'] = np.where(denom > 0, t_i * (m_i * temp_df['pop_m']) / denom, 0.0)
        
        for _, row in temp_df.iterrows():
            if row['T_hat_ij'] > 0:
                final_results.append({
                    'ORIGIN_ZONE': i_zone,
                    'DEST_SUBZONE': row['SUBZONE_C'],
                    'T_hat_ij': row['T_hat_ij']
                })

    # 5. Save Results
    results_df = pd.DataFrame(final_results)
    print(f"💾 Saving Step 6 results to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    total_predicted = results_df['T_hat_ij'].sum()
    print(f"✅ Step 6 Global Singapore Complete. Total Predicted Volume: {total_predicted:,.2f}")

if __name__ == "__main__":
    main()
