import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Files
ACTUAL_FILE = 'aggregated_trips.csv'
S3_FILE = 'step3_gravity_results.csv'
S4_FILE = 'step4_gravity_results.csv'
S6_FILE = 'step6_radiation_results.csv'
S8_FILE = 'step8_radiation_results.csv'
S7_PARAMS = 'step7_gravity_results.csv'
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
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
    ss_res = np.sum((y_true - y_pred)**2); ss_tot = np.sum((y_true - np.mean(y_true))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    return cpc, r2, mae, rmse

def main():
    print("🚀 Step 9 (SEOUL): Full 6-Model Comparative Analysis - j != i Constraint adhered")
    
    # 1. Load Geometries
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.replace('.0', '', regex=False)
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    all_zones = gdf_utm.index.values
    z_count = len(all_zones)
    zone_to_idx = {z: i for i, z in enumerate(all_zones)}
    coords = np.array([[p.x, p.y] for p in gdf_utm.geometry.centroid])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat)

    # 2. Load Actual Trips and Matrix
    actual_df_raw = pd.read_csv(ACTUAL_FILE)
    actual_df_raw['O'] = actual_df_raw['ORIGIN_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    actual_df_raw['D'] = actual_df_raw['DESTINATION_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    
    actual_matrix = np.zeros((z_count, z_count))
    for _, row in actual_df_raw.iterrows():
        if row['O'] in zone_to_idx and row['D'] in zone_to_idx:
            actual_matrix[zone_to_idx[row['O']], zone_to_idx[row['D']]] = row['COUNT']
            
    internal_flows = np.diag(actual_matrix)
    external_oi = actual_matrix.sum(axis=1) - internal_flows

    # 3. Load Shell/Radiation Model Predictions (which already include GT diagonal)
    def load_pred_full(f):
        if not os.path.exists(f): return None
        df = pd.read_csv(f)
        m = np.zeros((z_count, z_count))
        for _, row in df.iterrows():
            o = str(row['ORIGIN_ZONE']).strip().replace('.0', '')
            d = str(row['DEST_SUBZONE']).strip().replace('.0', '')
            c = row['T_hat_ij']
            if o in zone_to_idx and d in zone_to_idx:
                m[zone_to_idx[o], zone_to_idx[d]] = c
        return m

    m_uniform = load_pred_full(S3_FILE)
    m_weighted = load_pred_full(S4_FILE)
    m_radpop = load_pred_full(S6_FILE)
    m_radpoi = load_pred_full(S8_FILE)

    # 4. Generate Parametric flows with GT diagonal
    params = pd.read_csv(S7_PARAMS).set_index('ModelType')
    p_gamma = params.loc['Power-POI', 'Params']
    e_gamma = params.loc['Exp-POI', 'Params']
    
    # Needs POI for parametric weight
    poi_attr = pd.read_csv('pois_by_zone.csv')
    poi_attr['SUBZONE_C'] = poi_attr['SUBZONE_C'].astype(str).str.replace('.0', '', regex=False)
    aj_vec = np.array([poi_attr.set_index('SUBZONE_C')['A_j'].to_dict().get(z, 0.0) + 1.0 for z in all_zones])

    def solve_gravity(gamma, ftype='power'):
        decay = (1.0 / (dist_mat ** gamma)) if ftype == 'power' else np.exp(-gamma * dist_mat)
        weight_mat = decay * aj_vec[np.newaxis, :]
        np.fill_diagonal(weight_mat, 0)
        row_sums = weight_mat.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        prob_mat = weight_mat / row_sums
        return (prob_mat * external_oi[:, np.newaxis]) + np.diag(internal_flows)

    m_power = solve_gravity(p_gamma, 'power')
    m_exp = solve_gravity(e_gamma, 'exp')

    # 5. Evaluation
    comparison_results = []
    models = [
        ('Uniform', m_uniform), ('Weighted', m_weighted), 
        ('RadPop', m_radpop), ('RadPOI', m_radpoi),
        ('Power', m_power), ('Exp', m_exp)
    ]

    for idx, oz in enumerate(all_zones):
        if idx % 100 == 0: print(f"📍 Evaluating origin {idx}/{z_count}...")
        y_true = actual_matrix[idx, :]
        res = {'Zone': oz}
        for name, mat in models:
            if mat is None: continue
            y_pred = mat[idx, :]
            cpc, r2, mae, rmse = calculate_metrics(y_true, y_pred)
            res[f'{name}_CPC'] = cpc
            res[f'{name}_R2'] = r2
        comparison_results.append(res)

    results_df = pd.DataFrame(comparison_results)
    summary_data = []
    for m in [n for n, _ in models if _ is not None]:
        summary_data.append({
            'Model': m,
            'CPC': results_df[f'{m}_CPC'].mean(),
            'R2': results_df[f'{m}_R2'].mean()
        })
    summary_df = pd.DataFrame(summary_data)
    print("\n🏆 SUMMARY METRICS (SEOUL):")
    print(summary_df)
    
    results_df.to_csv(OUTPUT_METRICS, index=False)
    summary_df.to_csv(SUMMARY_METRICS, index=False)
    print(f"✅ Comparison complete. Results in {SUMMARY_METRICS}")

if __name__ == "__main__":
    main()
