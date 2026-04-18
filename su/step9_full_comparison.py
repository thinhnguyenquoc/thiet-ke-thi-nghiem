import pandas as pd
import geopandas as gpd
import numpy as np
import os
from PIL import Image
from shapely.geometry import Point

# Files
ACTUAL_FILE = 'aggregated_trips.csv'
S3_FILE = '../sgp/step3_gravity_results.csv' # Fallback or re-run
# Wait, su uses its own files
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
    print("🚀 Step 9: Full 6-Model Comparative Analysis (SEOUL)...")
    
    if not os.path.exists(S7_PARAMS):
        print(f"❌ Error: {S7_PARAMS} missing. Run Step 7 first.")
        return

    # 1. Load Actual Trips
    actual_df = pd.read_csv(ACTUAL_FILE)
    actual_df['ORIGIN'] = actual_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.replace('.0', '', regex=False)
    actual_df['DEST'] = actual_df['DESTINATION_SUBZONE'].astype(str).str.strip().str.replace('.0', '', regex=False)
    
    # 2. Load Existing Model Results
    print("📖 Loading Shell and Radiation results...")
    # Check if files exist to avoid crash
    for f in [S3_FILE, S4_FILE, S6_FILE, S8_FILE]:
        if not os.path.exists(f): 
            print(f"⚠️ Warning: {f} missing. Some comparisons will be skipped.")
    
    def load_pred(f):
        if not os.path.exists(f): return None
        df = pd.read_csv(f)
        df.rename(columns={'ORIGIN_ZONE': 'ORIGIN', 'DEST_SUBZONE': 'DEST'}, inplace=True, errors='ignore')
        df['ORIGIN'] = df['ORIGIN'].astype(str).str.strip().str.replace('.0', '', regex=False)
        df['DEST'] = df['DEST'].astype(str).str.strip().str.replace('.0', '', regex=False)
        return df

    s3_df = load_pred(S3_FILE)
    s4_df = load_pred(S4_FILE)
    s6_df = load_pred(S6_FILE) 
    s8_df = load_pred(S8_FILE) 

    # 3. Generate Parametric Decay Flows
    print("⚛️ Loading Production-Constrained Parametric parameters...")
    params = pd.read_csv(S7_PARAMS).set_index('ModelType')
    
    # Use POI versions for consistency with Shell models
    # Fallback to Pop version if POI missing
    p_key = 'Power-POI' if 'Power-POI' in params.index else 'Power-Pop'
    e_key = 'Exp-POI' if 'Exp-POI' in params.index else 'Exp-Pop'
    
    p_gamma = params.loc[p_key, 'gamma']
    e_gamma = params.loc[e_key, 'gamma']

    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.replace('.0', '', regex=False)
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    gdf_utm['cx'] = gdf_utm.geometry.centroid.x
    gdf_utm['cy'] = gdf_utm.geometry.centroid.y
    
    # Potential Attraction vectors
    # Step 9 logic usually uses same attraction as the model being compared
    poi_attr = pd.read_csv('pois_by_zone.csv')
    poi_attr['SUBZONE_C'] = poi_attr['SUBZONE_C'].astype(str).str.strip().str.replace('.0', '', regex=False)
    attr_dict = poi_attr.set_index('SUBZONE_C')['A_j'].to_dict()
    aj_vec = np.array([attr_dict.get(z, 0.0) + 1.0 for z in gdf_utm.index])

    all_zones = gdf_utm.index.values
    coords = gdf_utm[['cx', 'cy']].values
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat)

    def get_prob_mat(gamma, attr_vec, type='power'):
        if type == 'power':
            decay = attr_vec / (dist_mat ** gamma)
        else:
            decay = attr_vec * np.exp(-gamma * dist_mat)
        row_sums = decay.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return decay / row_sums

    print(f"   Using {p_key} (gamma={p_gamma:.4f}) and {e_key} (gamma={e_gamma:.4f})")
    prob_p = get_prob_mat(p_gamma, aj_vec, 'power')
    prob_e = get_prob_mat(e_gamma, aj_vec, 'exp')

    zone_to_idx = {z: i for i, z in enumerate(all_zones)}
    oi_series = actual_df.groupby('ORIGIN')['COUNT'].sum()

    # 4. Comparative Evaluation Loop
    unique_origins = actual_df['ORIGIN'].unique()
    final_rows = []

    for count, origin in enumerate(unique_origins):
        if count % 100 == 0: print(f"📍 Evaluating origin {count}/{len(unique_origins)}...")
        
        actual_z = actual_df[actual_df['ORIGIN'] == origin][['DEST', 'COUNT']].rename(columns={'COUNT': 'ACTUAL'})
        eval_dict = {'Zone': origin}
        
        # 1-4: Shell and Radiation
        models = [('Uniform', s3_df), ('Weighted', s4_df), ('RadPop', s6_df), ('RadPOI', s8_df)]
        for name, df in models:
            if df is None:
                eval_dict[f'{name}_CPC'] = 0; continue
            pred_z = df[df['ORIGIN'] == origin][['DEST', 'T_hat_ij']].rename(columns={'T_hat_ij': 'PRED'})
            merged = pd.merge(pred_z, actual_z, on='DEST', how='outer').fillna(0)
            eval_dict[f'{name}_CPC'], eval_dict[f'{name}_R2'], eval_dict[f'{name}_MAE'], eval_dict[f'{name}_RMSE'] = calculate_metrics(merged['ACTUAL'].values, merged['PRED'].values)
        
        # 5-6: Parametric
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
    metrics_list = ['CPC', 'R2', 'MAE', 'RMSE']
    model_names = ['Uniform', 'Weighted', 'RadPop', 'RadPOI', 'Power', 'Exp']
    
    summary_data = []
    for m in model_names:
        row = {'Model': m}
        for met in metrics_list:
            row[met] = results_df[f'{m}_{met}'].mean()
        summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    print("\n🏆 FINAL COMPARISON TABLE (SEOUL):")
    print(summary_df)
    
    results_df.to_csv(OUTPUT_METRICS, index=False)
    summary_df.to_csv(SUMMARY_METRICS, index=False)
    print(f"✅ Full metrics saved to {SUMMARY_METRICS}")

if __name__ == "__main__":
    main()
