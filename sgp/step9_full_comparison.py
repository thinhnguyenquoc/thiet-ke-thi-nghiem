import pandas as pd
import geopandas as gpd
import numpy as np
import os
from PIL import Image
from shapely.geometry import Point

# Files
ACTUAL_FILE = 'data_trip_sum.csv'
S3_FILE = 'step3_gravity_results.csv'
S4_FILE = 'step4_gravity_results.csv'
S6_FILE = 'step6_radiation_results.csv'
S8_FILE = 'step8_radiation_results.csv'
S7_PARAMS = 'step7_gravity_results.csv'

SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
POP_TIF = 'sgp_pop_2025_CN_1km_R2025A_UA_v1.tif'
POI_SUMMARY_FILE = 'pois_by_zone.csv'
CITY_CRS = 'EPSG:3414' 

OUTPUT_METRICS = 'step9_full_comparison.csv'
SUMMARY_METRICS = 'step9_summary_metrics.csv'

def calculate_metrics(y_true, y_pred):
    if len(y_true) == 0: return 0, 0, 0, 0
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
    print("🚀 Step 9: Full 8-Model Comparative Analysis (SINGAPORE)...")
    
    # 1. Load Actual Trips
    actual_df = pd.read_csv(ACTUAL_FILE)
    actual_df['ORIGIN'] = actual_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    actual_df['DEST'] = actual_df['DESTINATION_SUBZONE'].astype(str).str.strip().str.upper()
    
    # 2. Load Existing Model Results
    print("📖 Loading Shell and Radiation results...")
    s3_df = pd.read_csv(S3_FILE)
    s4_df = pd.read_csv(S4_FILE)
    s6_df = pd.read_csv(S6_FILE) 
    s8_df = pd.read_csv(S8_FILE) 
    
    for df in [s3_df, s4_df, s6_df, s8_df]:
        df.rename(columns={'ORIGIN_ZONE': 'ORIGIN', 'DEST_SUBZONE': 'DEST', 'T_hat_ij': 'PRED'}, inplace=True, errors='ignore')
        df['ORIGIN'] = df['ORIGIN'].astype(str).str.strip().str.upper()
        df['DEST'] = df['DEST'].astype(str).str.strip().str.upper()

    # Geometry and Data Mapping
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    
    poi_df = pd.read_csv(POI_SUMMARY_FILE)
    poi_df['SUBZONE_C'] = poi_df['SUBZONE_C'].astype(str).str.strip().str.upper()
    poi_lookup = poi_df.set_index('SUBZONE_C')['A_j'].to_dict()

    with Image.open(POP_TIF) as img:
        pop_data = np.array(img).astype(float)
        tiepoint = img.tag[33922]; pixel_scale = img.tag[33550]
        lons = tiepoint[3] + (np.arange(pop_data.shape[1]) + 0.5) * pixel_scale[0]
        lats = tiepoint[4] - (np.arange(pop_data.shape[0]) + 0.5) * pixel_scale[1]
        mask = (pop_data > 0) & (~np.isnan(pop_data))
        p_gdf = gpd.GeoDataFrame({'p': pop_data[mask]}, geometry=[Point(lons[c[1]], lats[c[0]]) for c in np.argwhere(mask)], crs="EPSG:4326")
        joined = gpd.sjoin(p_gdf, gdf.to_crs("EPSG:4326")[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
        joined['SUBZONE_C'] = joined['SUBZONE_C'].astype(str).str.strip().str.upper()
        zone_pop = joined.groupby('SUBZONE_C')['p'].sum().to_dict()

    # 3. Generate Parametric Decay Flows (Gravity PC)
    print("⚛️ Generating Production-Constrained Parametric flows...")
    params = pd.read_csv(S7_PARAMS).set_index('ModelType')
    
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    gdf_utm['cx'] = gdf_utm.geometry.centroid.x
    gdf_utm['cy'] = gdf_utm.geometry.centroid.y
    gdf_utm['pop'] = gdf_utm.index.map(zone_pop).fillna(0) + 1.0
    gdf_utm['poi'] = gdf_utm.index.map(poi_lookup).fillna(0) + 1.0 # B_j + 1
    
    all_zones = gdf_utm.index.values
    pop_vec = gdf_utm['pop'].values
    poi_vec = gdf_utm['poi'].values
    coords = gdf_utm[['cx', 'cy']].values
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat)

    def get_pred_mat(gamma, attr_vec, f_type='power'):
        decay = (attr_vec / (dist_mat ** gamma)) if f_type == 'power' else (attr_vec * np.exp(-gamma * dist_mat))
        row_sums = decay.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return decay / row_sums

    # Fixed keys check
    scenarios = {
        'Power-Pop': get_pred_mat(params.loc['Power-Pop', 'gamma'], pop_vec, 'power'),
        'Exp-Pop': get_pred_mat(params.loc['Exp-Pop', 'gamma'], pop_vec, 'exponential'),
        'Power-POI': get_pred_mat(params.loc['Power-POI', 'gamma'], poi_vec, 'power'),
        'Exp-POI': get_pred_mat(params.loc['Exp-POI', 'gamma'], poi_vec, 'exponential')
    }
    
    zone_to_idx = {z: i for i, z in enumerate(all_zones)}
    oi_series = actual_df.groupby('ORIGIN')['COUNT'].sum().to_dict()

    # 4. Evaluation Loop
    unique_origins = actual_df['ORIGIN'].unique()
    final_rows = []
    
    for count, origin in enumerate(unique_origins):
        if count % 100 == 0: print(f"📍 Evaluating origin {count}/{len(unique_origins)}...")
        actual_z = actual_df[actual_df['ORIGIN'] == origin][['DEST', 'COUNT']].rename(columns={'COUNT': 'ACTUAL'})
        eval_dict = {'Zone': origin}
        
        # Eval existing result files
        for name, df in [('Attr-Uniform', s3_df), ('Attr-Weighted', s4_df), ('RadPop', s6_df), ('RadPOI', s8_df)]:
            pred_z = df[df['ORIGIN'] == origin][['DEST', 'PRED']]
            merged = pd.merge(pred_z, actual_z, on='DEST', how='outer').fillna(0)
            eval_dict[f'{name}_CPC'], eval_dict[f'{name}_R2'], eval_dict[f'{name}_MAE'], eval_dict[f'{name}_RMSE'] = calculate_metrics(merged['ACTUAL'].values, merged['PRED'].values)
        
        # Eval generated parametric results
        o_idx = zone_to_idx.get(origin)
        if o_idx is not None:
            o_total = oi_series.get(origin, 0)
            for name, prob_mat in scenarios.items():
                p_preds = prob_mat[o_idx] * o_total
                merged = pd.merge(pd.DataFrame({'DEST': all_zones, 'PRED': p_preds}), actual_z, on='DEST', how='outer').fillna(0)
                eval_dict[f'{name}_CPC'], eval_dict[f'{name}_R2'], eval_dict[f'{name}_MAE'], eval_dict[f'{name}_RMSE'] = calculate_metrics(merged['ACTUAL'].values, merged['PRED'].values)
        
        final_rows.append(eval_dict)

    results_df = pd.DataFrame(final_rows)
    model_names = ['Attr-Uniform', 'Attr-Weighted', 'RadPop', 'RadPOI', 'Power-Pop', 'Exp-Pop', 'Power-POI', 'Exp-POI']
    summary_data = [{'Model': m, **{met: results_df[f'{m}_{met}'].mean() for met in ['CPC', 'R2', 'MAE', 'RMSE']}} for m in model_names]
    
    summary_df = pd.DataFrame(summary_data)
    print("\n🏆 FINAL SINGAPORE COMPARISON:\n", summary_df)
    results_df.to_csv(OUTPUT_METRICS, index=False)
    summary_df.to_csv(SUMMARY_METRICS, index=False)

if __name__ == "__main__":
    main()
