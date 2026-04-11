import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
POI_FILE = '../test-probability-distribution/detail_pois.geojson'
TRIPS_FILE = '../test-probability-distribution/data_trip_sum.csv'
BINNED_FILE = 'binned_trips_by_zone.csv'

# Output files mentioned in steps.md
STEP3_OUT = 'step3_gravity_results.csv'
STEP4_OUT = 'step4_gravity_results.csv'
STEP5_OUT = 'step5_gravity_results.csv'
STEP6_OUT = 'step6_evaluation_results.csv'

def calculate_models(origin_zones, trips_df, binned_df, gdf_meter):
    print(f"🚀 Running 3-Model Study for {len(origin_zones)} zones...")
    
    s3_res = [] # No POI (Equal)
    s4_res = [] # POI Weighted
    s5_res = [] # Only P_bin (Global Normalization)
    
    for i, origin_zone in enumerate(origin_zones):
        if i % 50 == 0: print(f"📍 Progress: {i}/{len(origin_zones)} zones...")
        
        o_i = trips_df[trips_df['ORIGIN_SUBZONE'] == origin_zone]['COUNT'].sum()
        zone_binned = binned_df[binned_df['ORIGIN_SUBZONE'] == origin_zone].copy()
        if zone_binned.empty: continue
        
        total_hist = zone_binned['COUNT'].sum()
        zone_binned['P_bin_k'] = zone_binned['COUNT'] / total_hist
        p_bin_lookup = zone_binned.set_index('distance_bin')['P_bin_k'].to_dict()

        origin_feat = gdf_meter[gdf_meter['SUBZONE_C'] == origin_zone]
        if origin_feat.empty: continue
        origin_point = origin_feat.centroid.values[0]

        # Geometry & Attributes
        temp_gdf = gdf_meter.copy()
        distances_km = temp_gdf.centroid.distance(origin_point).values / 1000.0
        bins_k = np.floor(distances_km).astype(float)
        
        # Aggregates for normalization
        temp_gdf['bin_k'] = bins_k
        bin_counts = temp_gdf.groupby('bin_k').size().to_dict()           # N_k
        bin_attraction = temp_gdf.groupby('bin_k')['A_j'].sum().to_dict() # Sum A_z
        
        # Pre-calculating Global Sum P(bin) for Step 5
        # Sum_z P(bin_z) = Sum_k (N_k * P_bin_k)
        global_sum_p_bin = sum(bin_counts.get(k, 0) * p_bin_lookup.get(k, 0.0) for k in p_bin_lookup)

        for idx, row in temp_gdf.iterrows():
            bin_id = bins_k[idx]
            p_bin = p_bin_lookup.get(bin_id, 0.0)
            if p_bin <= 0: continue
            
            # Step 3: No POI (Equal)
            t_hat_s3 = o_i * (p_bin / bin_counts[bin_id])
            s3_res.append({'ORIGIN_ZONE': origin_zone, 'DEST_SUBZONE': row['SUBZONE_C'], 'T_hat_ij': t_hat_s3})
            
            # Step 4: POI Weighted
            sum_az = bin_attraction.get(bin_id, 0.0)
            t_hat_s4 = o_i * p_bin * (row['A_j'] / sum_az) if sum_az > 0 else 0.0
            s4_res.append({'ORIGIN_ZONE': origin_zone, 'DEST_SUBZONE': row['SUBZONE_C'], 'T_hat_ij': t_hat_s4})
            
            # Step 5: Only P(bin) - Global Logic
            # Normalized to sum to O_i
            t_hat_s5 = o_i * (p_bin / global_sum_p_bin) if global_sum_p_bin > 0 else 0.0
            s5_res.append({'ORIGIN_ZONE': origin_zone, 'DEST_SUBZONE': row['SUBZONE_C'], 'T_hat_ij': t_hat_s5})
            
    return pd.DataFrame(s3_res), pd.DataFrame(s4_res), pd.DataFrame(s5_res)

def calculate_cpc(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    if total == 0: return 0
    return 2 * intersection / total

def main():
    print("🏗️ Building Full 3-Model Pipeline (Step 3, 4, 5, 6)")
    
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    
    binned_df = pd.read_csv(BINNED_FILE)
    binned_df['ORIGIN_SUBZONE'] = binned_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    
    gdf = gpd.read_file(POI_FILE)
    poi_cols = ['amenity', 'leisure', 'office', 'public_transport', 'shop', 'tourism']
    gdf['A_j'] = gdf[[c for c in poi_cols if c in gdf.columns]].sum(axis=1)
    gdf_meter = gdf.to_crs(epsg=3414)
    gdf_meter['SUBZONE_C'] = gdf_meter['SUBZONE_C'].astype(str).str.strip().str.upper()
    
    origin_zones = binned_df['ORIGIN_SUBZONE'].unique()
    
    # Calculate Models
    df3, df4, df5 = calculate_models(origin_zones, trips_df, binned_df, gdf_meter)
    
    # Save results
    print("💾 Saving gravity result files...")
    df3.to_csv(STEP3_OUT, index=False)
    df4.to_csv(STEP4_OUT, index=False)
    df5.to_csv(STEP5_OUT, index=False)
    
    # Step 6: Evaluation
    print("📊 Evaluating performance...")
    metrics = []
    
    actual_df = pd.read_csv(TRIPS_FILE)
    actual_df['ORIGIN_SUBZONE'] = actual_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    actual_df['DESTINATION_SUBZONE'] = actual_df['DESTINATION_SUBZONE'].astype(str).str.strip().str.upper()

    for zone in origin_zones:
        actual_zone = actual_df[actual_df['ORIGIN_SUBZONE'] == zone][['DESTINATION_SUBZONE', 'COUNT']]
        actual_zone.rename(columns={'COUNT': 'ACTUAL_FLOW'}, inplace=True)
        
        for name, pred_df in [('No POI (Eq)', df3), ('POI Weighted', df4), ('Global P_bin', df5)]:
            p_zone = pred_df[pred_df['ORIGIN_ZONE'] == zone][['DEST_SUBZONE', 'T_hat_ij']]
            merged = pd.merge(p_zone, actual_zone, left_on='DEST_SUBZONE', right_on='DESTINATION_SUBZONE', how='outer').fillna(0)
            
            y_true, y_pred = merged['ACTUAL_FLOW'].values, merged['T_hat_ij'].values
            cpc = calculate_cpc(y_true, y_pred)
            r2 = 1 - (np.sum((y_true - y_pred)**2) / np.sum((y_true - np.mean(y_true))**2)) if np.sum((y_true - np.mean(y_true))**2) > 0 else 0
            
            metrics.append({'Zone': zone, 'Model': name, 'CPC': cpc, 'R2': r2})
            
    eval_df = pd.DataFrame(metrics)
    summary = eval_df.groupby('Model').agg({'CPC': 'mean', 'R2': 'mean'}).reset_index()
    print("\n🌟 Aggregate Results:")
    print(summary.to_string(index=False))
    
    eval_df.to_csv(STEP6_OUT, index=False)
    print(f"✅ Full 3-Model pipeline complete. Results in {STEP6_OUT}")

if __name__ == "__main__":
    main()
