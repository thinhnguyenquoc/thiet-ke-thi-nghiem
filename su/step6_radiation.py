import pandas as pd
import geopandas as gpd
import numpy as np
import os
from PIL import Image
from shapely.geometry import Point

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
TRIPS_FILE = 'aggregated_trips.csv'
POP_TIF = 'kor_pop_2025_CN_1km_R2025A_UA_v1.tif'
OUTPUT_FILE = 'step6_radiation_results.csv'
CITY_CRS = 'EPSG:5179'  # Matching UTM-K used in previous steps

def main():
    print("🚀 Step 7: Radiation Model Implementation...")

    # 1. Load Geometries
    print("📖 Loading subzone geometries...")
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(float)
    
    # Calculate centroids for distances (in UTM-K for accuracy)
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    # Keep centroids in UTM-K for distance calculation later
    centroids_utm = gdf_utm.set_index('SUBZONE_C')['centroid'].to_dict()
    
    # 2. Extract Population per Zone
    print("📊 Extracting population from TIFF...")
    # Get TIFF metadata manually since rasterio is missing
    with Image.open(POP_TIF) as img:
        pop_data = np.array(img)
        # ModelTiepointTag: (0.0, 0.0, 0.0, Lon_orig, Lat_orig, 0.0)
        # ModelPixelScaleTag: (Scale_x, Scale_y, 0.0)
        tiepoint = img.tag[33922]
        pixel_scale = img.tag[33550]
        
        lon_orig = tiepoint[3]
        lat_orig = tiepoint[4]
        dx = pixel_scale[0]
        dy = pixel_scale[1]
        
        rows, cols = pop_data.shape
        
        # Create grid of lon/lat for pixel centers
        # Note: RasterPixelIsArea (tag 1025=1) means tiepoint is at the corner.
        # Pixel center is (col+0.5)*dx, (row+0.5)*dy offset from tiepoint.
        c_cols, r_rows = np.meshgrid(np.arange(cols), np.arange(rows))
        lons = lon_orig + (c_cols + 0.5) * dx
        lats = lat_orig - (r_rows + 0.5) * dy # Lat decreases as row increases
        
        # Filter out NoData or zero population pixels to speed up
        mask = (pop_data > 0) & (~np.isnan(pop_data))
        valid_pop = pop_data[mask]
        valid_lons = lons[mask]
        valid_lats = lats[mask]
        
    print(f"✨ Found {len(valid_pop)} pixels with population data.")
    
    # Map pixels to zones
    pixel_gdf = gpd.GeoDataFrame(
        {'pop': valid_pop}, 
        geometry=[Point(x, y) for x, y in zip(valid_lons, valid_lats)],
        crs="EPSG:4326"
    )
    
    # Ensure zone geometries are in EPSG:4326 for spatial join
    gdf_4326 = gdf.to_crs("EPSG:4326")
    
    print("📍 Spatial Join: Mapping pixels to subzones...")
    joined = gpd.sjoin(pixel_gdf, gdf_4326[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
    
    zone_pop = joined.groupby('SUBZONE_C')['pop'].sum().to_dict()
    
    # Assign population to GDF
    gdf_utm['pop_m'] = gdf_utm['SUBZONE_C'].map(zone_pop).fillna(0)
    
    print(f"📈 Total population mapped to zones: {gdf_utm['pop_m'].sum():,.0f}")
    
    # 3. Load Empirical Trips for T_i (Total departures)
    print("📖 Loading empirical trips...")
    trips_df = pd.read_csv(TRIPS_FILE)
    # T_i = Sum of trips FROM origin i
    t_i_df = trips_df.groupby('ORIGIN_SUBZONE')['COUNT'].sum().reset_index()
    t_i_lookup = t_i_df.set_index('ORIGIN_SUBZONE')['COUNT'].to_dict()
    
    # 4. Implement Radiation Model
    print("⚛️ Calculating Radiation Model predictions...")
    
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    zone_pop_dict = gdf_utm.set_index('SUBZONE_C')['pop_m'].to_dict()
    
    final_results = []
    
    # For optimization, pre-calculate all-to-all distances
    # But with 421 zones, we can do it origin-by-origin
    
    for count, i_zone in enumerate(unique_zones):
        if count % 50 == 0:
            print(f"📍 Processed {count}/{len(unique_zones)} origin zones...")
            
        t_i = t_i_lookup.get(i_zone, 0.0)
        if t_i == 0: continue
        
        m_i = zone_pop_dict.get(i_zone, 0.0)
        
        # Origin point
        p_i = centroids_utm[i_zone]
        
        # Calculate distances to all other zones
        temp_df = gdf_utm[gdf_utm['SUBZONE_C'] != i_zone].copy()
        temp_df['dist'] = temp_df['centroid'].distance(p_i)
        
        # Sort by distance to efficiently calculate s_ij
        temp_df = temp_df.sort_values('dist')
        
        # s_ij = sum of population in circle radius d_ij, excluding i and j.
        # Since we sorted by distance, s_ij for zone j is the sum of populations of all zones BEFORE j in the sorted list.
        # Excluding i? i is already excluded from temp_df.
        # Excluding j? The sum of pops BEFORE j doesn't include j.
        
        temp_df['s_ij'] = temp_df['pop_m'].shift(1).fillna(0).cumsum()
        
        # Radiation formula: T_ij = T_i * (m_i * n_j) / [(m_i + s_ij) * (m_i + n_j + s_ij)]
        # n_j is the population of destination zone j
        temp_df['T_hat_ij'] = t_i * (m_i * temp_df['pop_m']) / \
                              ((m_i + temp_df['s_ij']) * (m_i + temp_df['pop_m'] + temp_df['s_ij']))
        
        # Clean up: remove cases where denominator is zero (m_i + s_ij = 0)
        temp_df['T_hat_ij'] = temp_df['T_hat_ij'].fillna(0)
        
        for _, row in temp_df.iterrows():
            if row['T_hat_ij'] > 0:
                final_results.append({
                    'ORIGIN_ZONE': i_zone,
                    'DEST_SUBZONE': row['SUBZONE_C'],
                    'T_hat_ij': row['T_hat_ij']
                })

    # 5. Save Results
    results_df = pd.DataFrame(final_results)
    print(f"💾 Saving Step 7 results to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    total_predicted = results_df['T_hat_ij'].sum()
    print(f"✅ Step 7 Global Seoul Complete. Total Predicted Volume: {total_predicted:,.2f}")

if __name__ == "__main__":
    main()
