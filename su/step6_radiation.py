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
CITY_CRS = 'EPSG:4326'
PROJECTED_CRS = 'EPSG:5179'

def main():
    print("🚀 Step 6 (SEOUL): Radiation Model Implementation (j != i Constraint)")

    # 1. Load Geometries
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.replace('.0', '', regex=False)
    gdf_utm = gdf.to_crs(PROJECTED_CRS)
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    idx_to_zone = {i: z for i, z in enumerate(unique_zones)}
    
    # Extract Population per Zone
    with Image.open(POP_TIF) as img:
        pop_data = np.array(img).astype(float)
        tiepoint = img.tag[33922]; pixel_scale = img.tag[33550]
        lons = tiepoint[3] + (np.arange(pop_data.shape[1]) + 0.5) * pixel_scale[0]
        lats = tiepoint[4] - (np.arange(pop_data.shape[0]) + 0.5) * pixel_scale[1]
        mask = (pop_data > 0) & (~np.isnan(pop_data))
        pixel_gdf = gpd.GeoDataFrame({'pop': pop_data[mask]}, geometry=[Point(lons[c[1]], lats[c[0]]) for c in np.argwhere(mask)], crs="EPSG:4326")
    joined = gpd.sjoin(pixel_gdf, gdf[['SUBZONE_C', 'geometry']].to_crs("EPSG:4326"), how="inner", predicate="within")
    joined['SUBZONE_C'] = joined['SUBZONE_C'].astype(str).str.strip().str.replace('.0', '', regex=False)
    pop_vec = joined.groupby('SUBZONE_C')['pop'].sum().reindex(unique_zones).fillna(0).values + 1.0

    # 3. Load Trips and Handle Internal Flows
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    
    internal_lookup = trips_df[trips_df['ORIGIN_SUBZONE'] == trips_df['DESTINATION_SUBZONE']].set_index('ORIGIN_SUBZONE')['COUNT'].to_dict()
    external_trips = trips_df[trips_df['ORIGIN_SUBZONE'] != trips_df['DESTINATION_SUBZONE']]
    o_i_out_lookup = external_trips.groupby('ORIGIN_SUBZONE')['COUNT'].sum().to_dict()

    # Pre-calculate Distance Matrix
    coords = np.array([[p.x, p.y] for p in gdf_utm.geometry.centroid])
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
        
        # Sort indices by distance, excluding origin
        mask = np.ones(len(unique_zones), dtype=bool)
        mask[i_idx] = False
        valid_indices = np.arange(len(unique_zones))[mask]
        valid_dists = dists[mask]
        valid_pop = pop_vec[mask]
        
        sort_p_idx = np.argsort(valid_dists)
        sorted_pops = valid_pop[sort_p_idx]
        sorted_indices = valid_indices[sort_p_idx]
        
        # s_ij
        s_ij_vec = np.concatenate(([0], np.cumsum(sorted_pops)[:-1]))
        n_j = sorted_pops
        denom = (m_i + s_ij_vec) * (m_i + n_j + s_ij_vec)
        t_hat_ij_vec = np.where(denom > 0, o_i_out * (m_i * n_j) / denom, 0.0)
        
        for k, d_idx in enumerate(sorted_indices):
            if t_hat_ij_vec[k] > 1e-4:
                final_results.append({
                    'ORIGIN_ZONE': i_zone, 'DEST_SUBZONE': idx_to_zone[d_idx], 'T_hat_ij': t_hat_ij_vec[k]
                })

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 6 complete (Seoul). Internal flows preserved.")

if __name__ == "__main__":
    main()
