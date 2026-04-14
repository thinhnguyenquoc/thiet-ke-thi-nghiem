import pandas as pd
import geopandas as gpd
import numpy as np
import os
from PIL import Image
from shapely.geometry import Point
from scipy.optimize import minimize

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
TRIPS_FILE = 'data_trip_sum.csv'
POP_TIF = 'sgp_pop_2025_CN_1km_R2025A_UA_v1.tif'
POI_FILE = 'pois_by_zone.csv'
OUTPUT_FILE = 'step7_gravity_results.csv'
CITY_CRS = 'EPSG:3414'

def calculate_metrics(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    cpc = 2 * intersection / total if total > 0 else 0
    
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    return cpc, r2, mae, rmse

def main():
    print("🚀 Step 7 (SINGAPORE): Production-Constrained Gravity model (Pop vs POI)...")

    # 1. Load Geometries & Population
    print("📖 Loading subzone geometries...")
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    gdf_utm['centroid_x'] = gdf_utm.geometry.centroid.x
    gdf_utm['centroid_y'] = gdf_utm.geometry.centroid.y
    
    print("📊 Extracting population...")
    with Image.open(POP_TIF) as img:
        pop_data = np.array(img).astype(float)
        tiepoint = img.tag[33922]; pixel_scale = img.tag[33550]
        lons = tiepoint[3] + (np.arange(pop_data.shape[1]) + 0.5) * pixel_scale[0]
        lats = tiepoint[4] - (np.arange(pop_data.shape[0]) + 0.5) * pixel_scale[1]
        mask = (pop_data > 0)
        pixel_coords = np.argwhere(mask)
        pixel_gdf = gpd.GeoDataFrame({'pop': pop_data[mask]}, geometry=[Point(lons[c[1]], lats[c[0]]) for c in pixel_coords], crs="EPSG:4326")
    
    joined = gpd.sjoin(pixel_gdf, gdf.to_crs("EPSG:4326")[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
    zone_pop = joined.groupby('SUBZONE_C')['pop'].sum()
    gdf_utm['pop'] = zone_pop.fillna(0)

    # 2. Load POI Attraction
    print("🏪 Loading POI attractions...")
    if os.path.exists(POI_FILE):
        poi_df = pd.read_csv(POI_FILE)
        gdf_utm = gdf_utm.reset_index().merge(poi_df[['SUBZONE_C', 'A_j']], on='SUBZONE_C', how='left').fillna(1.0).set_index('SUBZONE_C')
    else:
        gdf_utm['A_j'] = 1.0
    
    # 3. Load Trips and calculate O_i
    print("📖 Loading empirical trips...")
    trips_df = pd.read_csv(TRIPS_FILE)
    oi_df = trips_df.groupby('ORIGIN_SUBZONE')['COUNT'].sum().rename('O_i')
    
    all_zones = gdf_utm.index.values
    pop_vec = gdf_utm['pop'].values 
    aj_vec = gdf_utm['A_j'].values
    
    # Pre-calculate Distance Matrix
    print("📏 Pre-calculating distance matrix...")
    coords = gdf_utm[['centroid_x', 'centroid_y']].values
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat) 
    
    zone_to_idx = {z: i for i, z in enumerate(all_zones)}
    actual_mat = np.zeros((len(all_zones), len(all_zones)))
    for _, row in trips_df.iterrows():
        if row['ORIGIN_SUBZONE'] in zone_to_idx and row['DESTINATION_SUBZONE'] in zone_to_idx:
            actual_mat[zone_to_idx[row['ORIGIN_SUBZONE']], zone_to_idx[row['DESTINATION_SUBZONE']]] = row['COUNT']
    
    def solve_model(gamma, attr_vec, type='power'):
        if type == 'power':
            decay = attr_vec / (dist_mat ** gamma)
        else:
            decay = attr_vec * np.exp(-gamma * dist_mat)
        
        row_sums = decay.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0 
        prob_mat = decay / row_sums
        
        pred_mat = np.zeros_like(prob_mat)
        for i, z in enumerate(all_zones):
            if z in oi_df:
                pred_mat[i, :] = prob_mat[i, :] * oi_df[z]
        return pred_mat

    def objective(gamma, attr_vec, type='power'):
        g = gamma[0] if isinstance(gamma, (list, np.ndarray)) else gamma
        pred_mat = solve_model(g, attr_vec, type)
        intersection = np.sum(np.minimum(actual_mat, pred_mat))
        total = np.sum(actual_mat) + np.sum(pred_mat)
        cpc = 2 * intersection / total if total > 0 else 0
        return 1.0 - cpc

    model_results = []
    scenarios = [
        ('Power-Pop', pop_vec, 'power', 1.5),
        ('Exp-Pop', pop_vec, 'exponential', 0.1),
        ('Power-POI', aj_vec, 'power', 1.5),
        ('Exp-POI', aj_vec, 'exponential', 0.1),
    ]

    for name, attr, ftype, x0 in scenarios:
        print(f"⚛️ Optimizing {name}...")
        res = minimize(objective, x0=[x0], args=(attr, ftype), bounds=[(0, 10)])
        gamma_opt = res.x[0]
        pred_mat = solve_model(gamma_opt, attr, ftype)
        cpc, r2, mae, rmse = calculate_metrics(actual_mat.flatten(), pred_mat.flatten())
        print(f"   Result: gamma={gamma_opt:.4f}, CPC={cpc:.4f}")
        model_results.append({'ModelType': name, 'gamma': gamma_opt, 'CPC': cpc, 'R2': r2})

    # 5. Save Results
    results_df = pd.DataFrame(model_results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print("\n📊 GRAVITY MODEL PARAMETERS (SINGAPORE):")
    print(results_df)

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
