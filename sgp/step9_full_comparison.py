import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Files
ACTUAL_FILE = 'data_trip_sum.csv'
S3_FILE = 'step3_gravity_results.csv'
S4_FILE = 'step4_gravity_results.csv'
S6_FILE = 'step6_radiation_results.csv'
S8_FILE = 'step8_radiation_results.csv'
S7_PARAMS = 'step7_gravity_results.csv'
SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
POI_SUMMARY_FILE = 'pois_by_zone.csv'
CITY_CRS = 'EPSG:3414' 
OUTPUT_METRICS = 'step9_full_comparison.csv'
SUMMARY_METRICS = 'step9_summary_metrics.csv'

def calculate_metrics(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    cpc = 2 * intersection / total if total > 0 else 0
    mae = np.mean(np.abs(y_true - y_pred))
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    return cpc, r2, mae

def main():
    print("🚀 Step 9 (SINGAPORE): Full Comparative Analysis - j != i Constraint Adhered")
    
    # 1. Load Geometries
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    gdf_utm = gdf.to_crs(CITY_CRS).set_index('SUBZONE_C')
    all_zones = gdf_utm.index.values
    z_count = len(all_zones)
    zone_to_idx = {z: i for i, z in enumerate(all_zones)}
    coords = np.array([[p.x, p.y] for p in gdf_utm.geometry.centroid])
    dist_mat = np.sqrt(np.sum((coords[:, np.newaxis, :] - coords[np.newaxis, :, :])**2, axis=2)) / 1000.0
    dist_mat = np.where(dist_mat < 0.01, 0.01, dist_mat)

    # 2. Load Actual Matrix
    actual_df = pd.read_csv(ACTUAL_FILE)
    actual_df['O'] = actual_df['ORIGIN_SUBZONE'].astype(str).str.upper()
    actual_df['D'] = actual_df['DESTINATION_SUBZONE'].astype(str).str.upper()
    
    actual_matrix = np.zeros((z_count, z_count))
    for _, row in actual_df.iterrows():
        if row['O'] in zone_to_idx and row['D'] in zone_to_idx:
            actual_matrix[zone_to_idx[row['O']], zone_to_idx[row['D']]] = row['COUNT']
            
    internal_flows = np.diag(actual_matrix)
    external_oi = actual_matrix.sum(axis=1) - internal_flows

    # 3. Load Model Predictions (already include GT diagonal)
    def load_pred_full(f):
        if not os.path.exists(f): return None
        df = pd.read_csv(f)
        m = np.zeros((z_count, z_count))
        for _, row in df.iterrows():
            o, d, c = str(row['ORIGIN_ZONE']), str(row['DEST_SUBZONE']), row['T_hat_ij']
            if o in zone_to_idx and d in zone_to_idx:
                m[zone_to_idx[o], zone_to_idx[d]] = c
        return m

    m_uniform = load_pred_full(S3_FILE)
    m_weighted = load_pred_full(S4_FILE)
    m_radpop = load_pred_full(S6_FILE)
    m_radpoi = load_pred_full(S8_FILE)

    # 4. Parametric flows with GT diagonal
    params = pd.read_csv(S7_PARAMS).set_index('ModelType')
    poi_attr = pd.read_csv(POI_SUMMARY_FILE)
    poi_attr['SUBZONE_C'] = poi_attr['SUBZONE_C'].astype(str).str.upper()
    aj_vec = np.array([poi_attr.set_index('SUBZONE_C')['A_j'].to_dict().get(z, 0.0) + 1.0 for z in all_zones])

    def solve_gravity(gamma, ftype='power'):
        decay = (1.0 / (dist_mat ** gamma)) if ftype == 'power' else np.exp(-gamma * dist_mat)
        weight_mat = decay * aj_vec[np.newaxis, :]
        np.fill_diagonal(weight_mat, 0)
        row_sums = weight_mat.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        prob_mat = weight_mat / row_sums
        return (prob_mat * external_oi[:, np.newaxis]) + np.diag(internal_flows)

    m_power = solve_gravity(params.loc['Power-POI', 'Params'], 'power')
    m_exp = solve_gravity(params.loc['Exp-POI', 'Params'], 'exp')

    # 5. Evaluation
    comparison_results = []
    models = [
        ('Uniform', m_uniform), ('Weighted', m_weighted), 
        ('RadPop', m_radpop), ('RadPOI', m_radpoi),
        ('Power', m_power), ('Exp', m_exp)
    ]

    for idx, oz in enumerate(all_zones):
        y_true = actual_matrix[idx, :]
        res = {'Zone': oz}
        for name, mat in models:
            if mat is None: continue
            y_pred = mat[idx, :]
            cpc, r2, mae = calculate_metrics(y_true, y_pred)
            res[f'{name}_CPC'] = cpc
            res[f'{name}_R2'] = r2
        comparison_results.append(res)

    results_df = pd.DataFrame(comparison_results)
    summary_data = [{'Model': n, 'CPC': results_df[f'{n}_CPC'].mean(), 'R2': results_df[f'{n}_R2'].mean()} for n, _ in models if _ is not None]
    summary_df = pd.DataFrame(summary_data)
    print("\n🏆 SUMMARY METRICS (SINGAPORE):\n", summary_df)
    
    results_df.to_csv(OUTPUT_METRICS, index=False)
    summary_df.to_csv(SUMMARY_METRICS, index=False)

if __name__ == "__main__":
    main()
