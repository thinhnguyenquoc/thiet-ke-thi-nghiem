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
CITY_CRS = 'EPSG:3414' # SVY21

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
    print("🚀 Step 9: Full 6-Model Comparative Analysis (SINGAPORE) with MAE/RMSE...")
    
    # 1. Load Actual Trips
    actual_df = pd.read_csv(ACTUAL_FILE)
    actual_df['ORIGIN'] = actual_df['ORIGIN_SUBZONE'].astype(str)
    actual_df['DEST'] = actual_df['DESTINATION_SUBZONE'].astype(str)
    
    # 2. Load Existing Model Results
    print("📖 Loading Shell and Radiation results...")
    s3_df = pd.read_csv(S3_FILE)
    s4_df = pd.read_csv(S4_FILE)
    s6_df = pd.read_csv(S6_FILE) 
    s8_df = pd.read_csv(S8_FILE) 
    
    for df in [s3_df, s4_df, s6_df, s8_df]:
        df.rename(columns={'ORIGIN_ZONE': 'ORIGIN', 'DEST_SUBZONE': 'DEST'}, inplace=True, errors='ignore')
        df['ORIGIN'] = df['ORIGIN'].astype(str)
        df['DEST'] = df['DEST'].astype(str)

    # 3. Generate Parametric Decay Flows (Power/Exponential)
    print("⚛️ Generating Parametric Decay flows for comparison...")
    params = pd.read_csv(S7_PARAMS).set_index('ModelType')
    
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str)
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    # Pop extraction
    with Image.open(POP_TIF) as img:
        pop_data = np.array(img).astype(float)
        tiepoint = img.tag[33922]; pixel_scale = img.tag[33550]
        lons = tiepoint[3] + (np.arange(pop_data.shape[1]) + 0.5) * pixel_scale[0]
        lats = tiepoint[4] - (np.arange(pop_data.shape[0]) + 0.5) * pixel_scale[1]
        mask = (pop_data > 0)
        pixel_gdf = gpd.GeoDataFrame({'pop': pop_data[mask]}, geometry=[Point(x, y) for (y, x) in [(l, ln) for l in lats for ln in lons if pop_data[np.where(lats==l)[0][0], np.where(lons==ln)[0][0]] > 0]], crs="EPSG:4326")
        joined = gpd.sjoin(pixel_gdf, gdf.to_crs("EPSG:4326")[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
        zone_pop = joined.groupby('SUBZONE_C')['pop'].sum().to_dict()
    
    gdf_utm['pop_m'] = gdf_utm['SUBZONE_C'].map(zone_pop).fillna(0)
    centroids = gdf_utm.set_index('SUBZONE_C')['centroid'].to_dict()
    pops = gdf_utm.set_index('SUBZONE_C')['pop_m'].to_dict()
    
    # 4. Evaluation Loop
    unique_origins = actual_df['ORIGIN'].unique()
    final_rows = []
    p_p = params.loc['Power']; p_e = params.loc['Exponential']

    for count, origin in enumerate(unique_origins):
        if count % 100 == 0: print(f"📍 Evaluating origin {count}/{len(unique_origins)}...")
        
        actual_z = actual_df[actual_df['ORIGIN'] == origin][['DEST', 'COUNT']].rename(columns={'COUNT': 'ACTUAL'})
        m_i = pops.get(origin, 0)
        c_i = centroids.get(origin)
        
        eval_dict = {'Zone': origin}
        models = [('Attr-Uniform', s3_df), ('Attr-Weighted', s4_df), ('RadPop', s6_df), ('RadPOI', s8_df)]
        
        for name, df in models:
            pred_z = df[df['ORIGIN'] == origin][['DEST', 'T_hat_ij']].rename(columns={'T_hat_ij': 'PRED'})
            merged = pd.merge(pred_z, actual_z, on='DEST', how='outer').fillna(0)
            eval_dict[f'{name}_CPC'], eval_dict[f'{name}_R2'], eval_dict[f'{name}_MAE'], eval_dict[f'{name}_RMSE'] = calculate_metrics(merged['ACTUAL'].values, merged['PRED'].values)
        
        # Parametric
        dest_zones = gdf_utm['SUBZONE_C'].values
        p_trips = []; e_trips = []
        for d_zone in dest_zones:
            if d_zone == origin or pops.get(d_zone, 0) == 0 or m_i == 0:
                p_trips.append(0); e_trips.append(0)
                continue
            r_ij = c_i.distance(centroids[d_zone]) / 1000.0
            if r_ij < 0.01: r_ij = 0.01
            p_trips.append(p_p['K'] * (m_i**p_p['alpha']) * (pops[d_zone]**p_p['beta']) / (r_ij**p_p['gamma']))
            e_trips.append(p_e['K'] * (m_i**p_e['alpha']) * (pops[d_zone]**p_e['beta']) * np.exp(-p_e['gamma'] * r_ij))
        
        # Power
        merged_p = pd.merge(pd.DataFrame({'DEST': dest_zones, 'PRED': p_trips}), actual_z, on='DEST', how='outer').fillna(0)
        eval_dict['Power_CPC'], eval_dict['Power_R2'], eval_dict['Power_MAE'], eval_dict['Power_RMSE'] = calculate_metrics(merged_p['ACTUAL'].values, merged_p['PRED'].values)
        # Exp
        merged_e = pd.merge(pd.DataFrame({'DEST': dest_zones, 'PRED': e_trips}), actual_z, on='DEST', how='outer').fillna(0)
        eval_dict['Exp_CPC'], eval_dict['Exp_R2'], eval_dict['Exp_MAE'], eval_dict['Exp_RMSE'] = calculate_metrics(merged_e['ACTUAL'].values, merged_e['PRED'].values)

        final_rows.append(eval_dict)

    summary_data = []
    results_df = pd.DataFrame(final_rows)
    model_names = ['Attr-Uniform', 'Attr-Weighted', 'RadPop', 'RadPOI', 'Power', 'Exp']
    for m in model_names:
        row = {'Model': m}
        for met in ['CPC', 'R2', 'MAE', 'RMSE']:
            row[met] = results_df[f'{m}_{met}'].mean()
        summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    print("\n🏆 FINAL SINGAPORE COMPARISON:")
    print(summary_df)
    
    results_df.to_csv(OUTPUT_METRICS, index=False)
    summary_df.to_csv(SUMMARY_METRICS, index=False)

if __name__ == "__main__":
    main()
