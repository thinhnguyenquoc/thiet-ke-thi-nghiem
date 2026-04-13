import pandas as pd
import geopandas as gpd
import numpy as np
import os
from PIL import Image
from shapely.geometry import Point

# Files
ACTUAL_FILE = 'aggregated_trips.csv'
S3_FILE = 'step3_gravity_results.csv'
S4_FILE = 'step4_gravity_results.csv'
S6_FILE = 'step6_radiation_results.csv'
S8_FILE = 'step8_radiation_results.csv'
S7_PARAMS = 'step7_gravity_results.csv'

SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
POP_TIF = 'kor_pop_2025_CN_1km_R2025A_UA_v1.tif'
CITY_CRS = 'EPSG:5179'

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
    print("🚀 Step 9: Full 6-Model Comparative Analysis (SEOUL) with MAE/RMSE...")
    
    # 1. Load Actual Trips
    actual_df = pd.read_csv(ACTUAL_FILE)
    actual_df['ORIGIN'] = actual_df['ORIGIN_SUBZONE'].astype(float).astype(int).astype(str)
    actual_df['DEST'] = actual_df['DESTINATION_SUBZONE'].astype(float).astype(int).astype(str)
    
    # 2. Load Existing Model Results
    print("📖 Loading Shell and Radiation results...")
    s3_df = pd.read_csv(S3_FILE)
    s4_df = pd.read_csv(S4_FILE)
    s6_df = pd.read_csv(S6_FILE) 
    s8_df = pd.read_csv(S8_FILE) 
    
    for df in [s3_df, s4_df, s6_df, s8_df]:
        df.rename(columns={'ORIGIN_ZONE': 'ORIGIN', 'DEST_SUBZONE': 'DEST'}, inplace=True, errors='ignore')
        df['ORIGIN'] = df['ORIGIN'].astype(float).astype(int).astype(str)
        df['DEST'] = df['DEST'].astype(float).astype(int).astype(str)

    # 3. Generate Parametric Decay Flows (Power/Exponential)
    print("⚛️ Generating Production-Constrained Parametric flows...")
    params = pd.read_csv(S7_PARAMS).set_index('ModelType')
    
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str)
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    gdf_utm['cx'] = gdf_utm.geometry.centroid.x
    gdf_utm['cy'] = gdf_utm.geometry.centroid.y
    
    # Simple population extraction from TIFF for Step 9
    with Image.open(POP_TIF) as img:
        pop_data = np.array(img).astype(float)
        tiepoint = img.tag[33922]; pixel_scale = img.tag[33550]
        lons = tiepoint[3] + (np.arange(pop_data.shape[1]) + 0.5) * pixel_scale[0]
        lats = tiepoint[4] - (np.arange(pop_data.shape[0]) + 0.5) * pixel_scale[1]
        mask = (pop_data > 0)
        p_coords = np.argwhere(mask)
        p_gdf = gpd.GeoDataFrame({'p': pop_data[mask]}, geometry=[Point(lons[c[1]], lats[c[0]]) for c in p_coords], crs="EPSG:4326")
        joined = gpd.sjoin(p_gdf, gdf.to_crs("EPSG:4326")[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
        zone_pop = joined.groupby('SUBZONE_C')['p'].sum().to_dict()

    gdf_utm['pop'] = gdf_utm.index.map(zone_pop).fillna(0)
    
    all_zones = gdf_utm.index.values
    pop_vec = gdf_utm['pop'].values
    coords = gdf_utm[['cx', 'cy']].values
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat)

    # 4. Comparative Evaluation Loop
    unique_origins = actual_df['ORIGIN'].unique()
    final_rows = []

    p_p = params.loc['Power']; p_e = params.loc['Exponential']

    # Pre-calculate full matrices for efficiency
    def get_pred_mat(gamma, type='power'):
        if type == 'power':
            decay = pop_vec / (dist_mat ** gamma)
        else:
            decay = pop_vec * np.exp(-gamma * dist_mat)
        row_sums = decay.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        prob_mat = decay / row_sums
        return prob_mat

    prob_p = get_pred_mat(p_p['gamma'], 'power')
    prob_e = get_pred_mat(p_e['gamma'], 'exp')

    zone_to_idx = {z: i for i, z in enumerate(all_zones)}
    oi_series = actual_df.groupby('ORIGIN')['COUNT'].sum()

    for count, origin in enumerate(unique_origins):
        if count % 100 == 0: print(f"📍 Evaluating origin {count}/{len(unique_origins)}...")
        
        actual_z = actual_df[actual_df['ORIGIN'] == origin][['DEST', 'COUNT']].rename(columns={'COUNT': 'ACTUAL'})
        eval_dict = {'Zone': origin}
        
        # 1-4: Load pre-calculated from CSVs
        models = [('Uniform', s3_df), ('Weighted', s4_df), ('RadPop', s6_df), ('RadPOI', s8_df)]
        for name, df in models:
            pred_z = df[df['ORIGIN'] == origin][['DEST', 'T_hat_ij']].rename(columns={'T_hat_ij': 'PRED'})
            merged = pd.merge(pred_z, actual_z, on='DEST', how='outer').fillna(0)
            eval_dict[f'{name}_CPC'], eval_dict[f'{name}_R2'], eval_dict[f'{name}_MAE'], eval_dict[f'{name}_RMSE'] = calculate_metrics(merged['ACTUAL'].values, merged['PRED'].values)
        
        # 5-6: Production-Constrained Power/Exp using pre-calculated probability matrices
        o_idx = zone_to_idx.get(origin)
        if o_idx is not None:
            o_total = oi_series.get(origin, 0)
            
            # Power
            p_preds = prob_p[o_idx] * o_total
            merged_p = pd.merge(pd.DataFrame({'DEST': all_zones, 'PRED': p_preds}), actual_z, on='DEST', how='outer').fillna(0)
            eval_dict['Power_CPC'], eval_dict['Power_R2'], eval_dict['Power_MAE'], eval_dict['Power_RMSE'] = calculate_metrics(merged_p['ACTUAL'].values, merged_p['PRED'].values)
            
            # Exp
            e_preds = prob_e[o_idx] * o_total
            merged_e = pd.merge(pd.DataFrame({'DEST': all_zones, 'PRED': e_preds}), actual_z, on='DEST', how='outer').fillna(0)
            eval_dict['Exp_CPC'], eval_dict['Exp_R2'], eval_dict['Exp_MAE'], eval_dict['Exp_RMSE'] = calculate_metrics(merged_e['ACTUAL'].values, merged_e['PRED'].values)
        
        final_rows.append(eval_dict)
    results_df = pd.DataFrame(final_rows)
    metrics = ['CPC', 'R2', 'MAE', 'RMSE']
    model_names = ['Uniform', 'Weighted', 'RadPop', 'RadPOI', 'Power', 'Exp']
    
    summary_data = []
    for m in model_names:
        row = {'Model': m}
        for met in metrics:
            row[met] = results_df[f'{m}_{met}'].mean()
        summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    print("\n🏆 FINAL COMPARISON TABLE:")
    print(summary_df)
    
    results_df.to_csv(OUTPUT_METRICS, index=False)
    summary_df.to_csv(SUMMARY_METRICS, index=False)
    print(f"✅ Full metrics saved to {SUMMARY_METRICS}")

if __name__ == "__main__":
    main()
