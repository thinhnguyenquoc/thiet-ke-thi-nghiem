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
    print("🚀 Step 6 (SINGAPORE): Radiation Model Implementation (Population)...")

    # 1. Load Geometries
    print("📖 Loading subzone geometries...")
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    
    # Calculate centroids
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    zone_to_idx = {z: i for i, z in enumerate(unique_zones)}
    idx_to_zone = {i: z for i, z in enumerate(unique_zones)}
    centroids = gdf_utm.set_index('SUBZONE_C')['centroid']
    
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
        
    pixel_gdf = gpd.GeoDataFrame(
        {'pop': valid_pop}, 
        geometry=[Point(x, y) for x, y in zip(valid_lons, valid_lats)],
        crs="EPSG:4326"
    )
    
    gdf_4326 = gdf.to_crs("EPSG:4326")
    joined = gpd.sjoin(pixel_gdf, gdf_4326[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
    joined['SUBZONE_C'] = joined['SUBZONE_C'].astype(str).str.strip().str.upper()
    zone_pop = joined.groupby('SUBZONE_C')['pop'].sum().to_dict()
    
    pop_vec = np.array([zone_pop.get(z, 0.0) for z in unique_zones]) + 1.0
    print(f"📈 Total population mapped to zones: {pop_vec.sum():,.0f}")
    
    # 3. Load Empirical Trips for T_i
    print("📖 Loading empirical trips...")
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    t_i_lookup = trips_df.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()
    
    # Pre-calculate Distance Matrix
    print("📏 Pre-calculating distance matrix...")
    coords = np.array([[p.x, p.y] for p in gdf_utm['centroid']])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    
    # 4. Implement Radiation Model
    print("⚛️ Calculating Radiation Model predictions...")
    final_results = []
    
    for i_idx, i_zone in enumerate(unique_zones):
        if i_idx % 100 == 0:
            print(f"📍 Processed {i_idx}/{len(unique_zones)} origin zones...")
            
        t_i = t_i_lookup.get(i_zone, 0.0)
        if t_i == 0: continue
        
        m_i = pop_vec[i_idx]
        if m_i == 0: continue # In classic radiation, m_i=0 makes T_ij=0
        
        # Distances from origin i_idx to all other zones
        dists = dist_mat[i_idx]
        
        # Create temp series to calculate s_ij
        # Sort indices by distance, excluding origin
        mask = np.ones(len(unique_zones), dtype=bool)
        mask[i_idx] = False
        
        valid_indices = np.arange(len(unique_zones))[mask]
        valid_dists = dists[mask]
        valid_pop = pop_vec[mask]
        
        # Sort valid indices by distance
        sort_idx = np.argsort(valid_dists)
        sorted_pops = valid_pop[sort_idx]
        sorted_indices = valid_indices[sort_idx]
        
        # s_ij = Sum of populations closer than j
        s_ij_vec = np.concatenate(([0], np.cumsum(sorted_pops)[:-1]))
        
        # Radiation formula
        n_j = sorted_pops
        denom = (m_i + s_ij_vec) * (m_i + n_j + s_ij_vec)
        t_hat_ij_vec = np.where(denom > 0, t_i * (m_i * n_j) / denom, 0.0)
        
        for k, d_idx in enumerate(sorted_indices):
            if t_hat_ij_vec[k] > 1e-6:
                final_results.append({
                    'ORIGIN_ZONE': i_zone,
                    'DEST_SUBZONE': idx_to_zone[d_idx],
                    'T_hat_ij': t_hat_ij_vec[k]
                })

    # 5. Save Results
    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 6 complete. Total Predicted Volume: {results_df['T_hat_ij'].sum():,.2f}")

if __name__ == "__main__":
    main()
