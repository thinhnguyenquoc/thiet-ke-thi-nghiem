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
POI_SUMMARY_FILE = 'pois_by_zone.csv'
OUTPUT_FILE = 'step7_gravity_results.csv'
CITY_CRS = 'EPSG:3414'
EPSILON = 1.0

def calculate_metrics(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    cpc = 2 * intersection / total if total > 0 else 0
    return cpc

def main():
    print("🚀 Step 7 (SINGAPORE): Gravity Model Implementation (j != i Constraint)")

    # 1. Load Data
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    
    # Extract Population
    with Image.open(POP_TIF) as img:
        pop_data = np.array(img).astype(float)
        tiepoint = img.tag[33922]; pixel_scale = img.tag[33550]
        lons = tiepoint[3] + (np.arange(pop_data.shape[1]) + 0.5) * pixel_scale[0]
        lats = tiepoint[4] - (np.arange(pop_data.shape[0]) + 0.5) * pixel_scale[1]
        mask = (pop_data > 0) & (~np.isnan(pop_data))
        pixel_gdf = gpd.GeoDataFrame({'pop': pop_data[mask]}, geometry=[Point(lons[c[1]], lats[c[0]]) for c in np.argwhere(mask)], crs="EPSG:4326")
    gdf_4326 = gdf.to_crs("EPSG:4326")
    joined = gpd.sjoin(pixel_gdf, gdf_4326[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
    joined['SUBZONE_C'] = joined['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_utm['pop'] = joined.groupby('SUBZONE_C')['pop'].sum().reindex(gdf_utm.index).fillna(0) + 1.0

    # Load POI
    poi_df = pd.read_csv(POI_SUMMARY_FILE)
    poi_df['SUBZONE_C'] = poi_df['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_utm['A_j'] = gdf_utm.index.map(poi_df.set_index('SUBZONE_C')['A_j']).fillna(0) + EPSILON
    
    # Load Trips and Handle Internal Flows
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(str).str.strip().str.upper()
    
    unique_zones = gdf_utm.index.values
    z_count = len(unique_zones)
    zone_to_idx = {z: i for i, z in enumerate(unique_zones)}
    
    actual_mat_total = np.zeros((z_count, z_count))
    for _, row in trips_df.iterrows():
        oz, dz = row['ORIGIN_SUBZONE'], row['DESTINATION_SUBZONE']
        if oz in zone_to_idx and dz in zone_to_idx:
            actual_mat_total[zone_to_idx[oz], zone_to_idx[dz]] = row['COUNT']
    
    internal_flows = np.diag(actual_mat_total)
    external_oi = actual_mat_total.sum(axis=1) - internal_flows
    
    coords = np.array([[p.x, p.y] for p in gdf_utm.geometry.centroid])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat)
    
    def solve_model(gamma, attr_vec, ftype='power'):
        if ftype == 'power':
            decay = 1.0 / (dist_mat ** gamma)
        else:
            decay = np.exp(-gamma * dist_mat)
        
        # Apply attraction weight B_j
        weight_mat = decay * attr_vec[np.newaxis, :]
        
        # EXCLUDE DIAGONAL (j != i)
        np.fill_diagonal(weight_mat, 0)
        
        # Normalize
        row_sums = weight_mat.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        prob_mat = weight_mat / row_sums
        
        # Predict flows based on O_i^out
        pred_mat_ext = prob_mat * external_oi[:, np.newaxis]
        
        # Add ground truth internal flows
        pred_mat_full = pred_mat_ext + np.diag(internal_flows)
        return pred_mat_full

    def objective(gamma, attr_vec, ftype='power'):
        pm = solve_model(gamma[0], attr_vec, ftype)
        return 1.0 - calculate_metrics(actual_mat_total, pm)

    scenarios = [
        ('Power-Pop', gdf_utm['pop'].values, 'power', 1.5),
        ('Exp-Pop', gdf_utm['pop'].values, 'exponential', 0.1),
        ('Power-POI', gdf_utm['A_j'].values, 'power', 1.5),
        ('Exp-POI', gdf_utm['A_j'].values, 'exponential', 0.1),
    ]

    model_results = []
    for name, attr, ftype, x0 in scenarios:
        print(f"⚛️ Optimizing {name}...")
        res = minimize(objective, x0=[x0], args=(attr, ftype), bounds=[(0.01, 10)])
        gamma_opt = res.x[0]
        pm = solve_model(gamma_opt, attr, ftype)
        cpc = calculate_metrics(actual_mat_total, pm)
        print(f"   Result: params={gamma_opt:.4f}, CPC={cpc:.4f}")
        model_results.append({'ModelType': name, 'Params': gamma_opt, 'CPC': cpc})

    pd.DataFrame(model_results).to_csv(OUTPUT_FILE, index=False)
    print("✅ Step 7 complete. Internal flows preserved as ground truth.")

if __name__ == "__main__":
    main()
