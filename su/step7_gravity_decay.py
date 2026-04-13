import pandas as pd
import geopandas as gpd
import numpy as np
import os
from PIL import Image
from shapely.geometry import Point
from scipy.optimize import minimize
from sklearn.metrics import r2_score

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
TRIPS_FILE = 'aggregated_trips.csv'
POP_TIF = 'kor_pop_2025_CN_1km_R2025A_UA_v1.tif'
OUTPUT_FILE = 'step7_gravity_results.csv'
CITY_CRS = 'EPSG:5179'

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
    print("🚀 Step 7: Production-Constrained Gravity model...")

    # 1. Load Geometries & Population
    print("📖 Loading subzone geometries...")
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(float)
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    gdf_utm['centroid_x'] = gdf_utm.geometry.centroid.x
    gdf_utm['centroid_y'] = gdf_utm.geometry.centroid.y
    
    # 2. Extract Population (minified)
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
    gdf_utm['pop'] = zone_pop
    gdf_utm['pop'] = gdf_utm['pop'].fillna(0)
    
    # 3. Load Trips and calculate O_i
    print("📖 Loading empirical trips...")
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(float)
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(float)
    
    oi_df = trips_df.groupby('ORIGIN_SUBZONE')['COUNT'].sum().rename('O_i')
    all_zones = gdf_utm.index.values
    pop_vec = gdf_utm['pop'].values # Vector of n_j
    
    # Pre-calculate Distance Matrix (all zones to all zones)
    print("📏 Pre-calculating distance matrix (421x421)...")
    coords = gdf_utm[['centroid_x', 'centroid_y']].values
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat) # Avoid division by zero
    
    # Map zones to indices
    zone_to_idx = {z: i for i, z in enumerate(all_zones)}
    
    # Actual OD matrix for comparison
    actual_mat = np.zeros((len(all_zones), len(all_zones)))
    for _, row in trips_df.iterrows():
        if row['ORIGIN_SUBZONE'] in zone_to_idx and row['DESTINATION_SUBZONE'] in zone_to_idx:
            actual_mat[zone_to_idx[row['ORIGIN_SUBZONE']], zone_to_idx[row['DESTINATION_SUBZONE']]] = row['COUNT']
    
    observed_origins = oi_df.index.values
    observed_oit = oi_df.values
    
    # 4. Optimization Functions (ONLY Gamma is a parameter, D_j = pop_vec)
    def solve_model(gamma, type='power'):
        if type == 'power':
            decay = pop_vec / (dist_mat ** gamma)
        else:
            decay = pop_vec * np.exp(-gamma * dist_mat)
        
        # Row-wise normalization (A_i calculation)
        row_sums = decay.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0 # Avoid div by zero
        prob_mat = decay / row_sums
        
        # Multiply by O_i
        pred_mat = np.zeros_like(prob_mat)
        for i, z in enumerate(all_zones):
            if z in oi_df:
                pred_mat[i, :] = prob_mat[i, :] * oi_df[z]
        return pred_mat

    def objective(gamma, type='power'):
        # gamma is passed as a single value by minimize if provided correctly or a list
        g = gamma[0] if isinstance(gamma, (list, np.ndarray)) else gamma
        pred_mat = solve_model(g, type)
        intersection = np.sum(np.minimum(actual_mat, pred_mat))
        total = np.sum(actual_mat) + np.sum(pred_mat)
        cpc = 2 * intersection / total if total > 0 else 0
        return 1.0 - cpc

    model_results = []
    
    # --- POWER LAW ---
    print("⚛️ Optimizing Production-Constrained Power Law (Only gamma)...")
    res_p = minimize(objective, x0=[1.5], args=('power',), bounds=[(0, 10)])
    gamma_p = res_p.x[0]
    pred_p = solve_model(gamma_p, 'power')
    cpc_p, r2_p, mae_p, rmse_p = calculate_metrics(actual_mat.flatten(), pred_p.flatten())
    print(f"   Result: gamma={gamma_p:.4f}, CPC={cpc_p:.4f}")
    model_results.append({'ModelType': 'Power', 'beta': 1.0, 'gamma': gamma_p, 'CPC': cpc_p})

    # --- EXPONENTIAL ---
    print("⚛️ Optimizing Production-Constrained Exponential (Only gamma)...")
    res_e = minimize(objective, x0=[0.1], args=('exponential',), bounds=[(0, 10)])
    gamma_e = res_e.x[0]
    pred_e = solve_model(gamma_e, 'exponential')
    cpc_e, r2_e, mae_e, rmse_e = calculate_metrics(actual_mat.flatten(), pred_e.flatten())
    print(f"   Result: gamma={gamma_e:.4f}, CPC={cpc_e:.4f}")
    model_results.append({'ModelType': 'Exponential', 'beta': 1.0, 'gamma': gamma_e, 'CPC': cpc_e})

    # 5. Save Results
    results_df = pd.DataFrame(model_results)
    print(f"💾 Saving Step 7 results to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n📊 GRAVITY MODEL PARAMETERS (Production-Constrained, Fixed Attractions):")
    print(results_df)
    print(f"✅ Step 7 Complete.")

if __name__ == "__main__":
    main()
