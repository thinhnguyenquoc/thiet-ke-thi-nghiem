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
CITY_CRS = 'EPSG:3414'

def main():
    print("🚀 Step 6 (SINGAPORE): Radiation Model Implementation (j != i Constraint)")

    # 1. Load Geometries
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    zone_to_idx = {z: i for i, z in enumerate(unique_zones)}
    idx_to_zone = {i: z for i, z in enumerate(unique_zones)}
    
    # 2. Extract Population per Zone
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
    
    # 3. Load Trips and Handle Internal Flows
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(str).str.strip().str.upper()
    
    internal_lookup = trips_df[trips_df['ORIGIN_SUBZONE'] == trips_df['DESTINATION_SUBZONE']].set_index('ORIGIN_SUBZONE')['COUNT'].to_dict()
    external_trips = trips_df[trips_df['ORIGIN_SUBZONE'] != trips_df['DESTINATION_SUBZONE']]
    o_i_out_lookup = external_trips.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()

    # Pre-calculate Distance Matrix
    coords = np.array([[p.x, p.y] for p in gdf_utm['centroid']])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    
    # 4. Implement Radiation Model for j != i
    print("⚛️ Calculating Radiation Model predictions...")
    final_results = []
    
    for i_idx, i_zone in enumerate(unique_zones):
        # A. Ground Truth Internal Flow
        t_ii = internal_lookup.get(i_zone, 0.0)
        final_results.append({'ORIGIN_ZONE': i_zone, 'DEST_SUBZONE': i_zone, 'T_hat_ij': t_ii})

        # B. Predicted External Flows
        o_i_out = o_i_out_lookup.get(i_zone, 0.0)
        if o_i_out == 0: continue
        
        m_i = pop_vec[i_idx]
        dists = dist_mat[i_idx]
        
        # Sort indices by distance, excluding origin i_idx
        mask = np.ones(len(unique_zones), dtype=bool)
        mask[i_idx] = False
        
        valid_indices = np.arange(len(unique_zones))[mask]
        valid_dists = dists[mask]
        valid_pop = pop_vec[mask]
        
        sort_p_idx = np.argsort(valid_dists)
        sorted_pops = valid_pop[sort_p_idx]
        sorted_indices = valid_indices[sort_p_idx]
        
        # s_ij = Sum of populations closer than j
        s_ij_vec = np.concatenate(([0], np.cumsum(sorted_pops)[:-1]))
        
        n_j = sorted_pops
        denom = (m_i + s_ij_vec) * (m_i + n_j + s_ij_vec)
        t_hat_ij_vec = np.where(denom > 0, o_i_out * (m_i * n_j) / denom, 0.0)
        
        for k, d_idx in enumerate(sorted_indices):
            if t_hat_ij_vec[k] > 1e-6:
                final_results.append({
                    'ORIGIN_ZONE': i_zone, 'DEST_SUBZONE': idx_to_zone[d_idx], 'T_hat_ij': t_hat_ij_vec[k]
                })

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 6 complete. Internal flows preserved as ground truth.")

if __name__ == "__main__":
    main()
