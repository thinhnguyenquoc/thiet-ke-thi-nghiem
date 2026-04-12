import pandas as pd
import numpy as np
import os

# Configuration
ACTUAL_FILE = 'aggregated_trips.csv'
S3_FILE = 'step3_gravity_results.csv'
S4_FILE = 'step4_gravity_results.csv'
S5_FILE = 'step5_gravity_results.csv'
OUTPUT_FILE = 'step6_evaluation_comparison.csv'

def calculate_cpc(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    if total == 0: return 0
    return 2 * intersection / total

def main():
    print("🚀 Step 6 (SEOUL FULL Comparison): Comparing all 3 Models...")

    if not all(os.path.exists(f) for f in [ACTUAL_FILE, S3_FILE, S4_FILE, S5_FILE]):
        print(f"❌ Error: Required result files missing.")
        return

    # 1. Load Data
    actual_df = pd.read_csv(ACTUAL_FILE)
    actual_df['ORIGIN_SUBZONE'] = actual_df['ORIGIN_SUBZONE'].astype(float)
    actual_df['DESTINATION_SUBZONE'] = actual_df['DESTINATION_SUBZONE'].astype(float)
    
    s3_df = pd.read_csv(S3_FILE) # No POI
    s4_df = pd.read_csv(S4_FILE) # POI Weighted
    s5_df = pd.read_csv(S5_FILE) # Global P_bin
    
    unique_origins = s3_df['ORIGIN_ZONE'].unique()
    print(f"📊 Analyzing {len(unique_origins)} zones.")

    final_metrics = []

    # 2. Iterate and compare
    for i, origin in enumerate(unique_origins):
        if i % 100 == 0: print(f"🕵️ Progress: {i}/{len(unique_origins)}...")
        
        actual_z = actual_df[actual_df['ORIGIN_SUBZONE'] == origin][['DESTINATION_SUBZONE', 'COUNT']]
        actual_z.rename(columns={'COUNT': 'ACTUAL_FLOW'}, inplace=True)
        
        # Model predictions
        results = []
        for name, pdf in [('No POI', s3_df), ('POI', s4_df), ('Global P_bin', s5_df)]:
            p_zone = pdf[pdf['ORIGIN_ZONE'] == origin][['DEST_SUBZONE', 'T_hat_ij']]
            merged = pd.merge(p_zone, actual_z, left_on='DEST_SUBZONE', right_on='DESTINATION_SUBZONE', how='outer').fillna(0)
            cpc = calculate_cpc(merged['ACTUAL_FLOW'].values, merged['T_hat_ij'].values)
            results.append(cpc)
            
        final_metrics.append({
            'Zone': origin,
            'CPC_No_POI': results[0],
            'CPC_POI': results[1],
            'CPC_Global': results[2]
        })

    # 3. Aggregated Summary
    results_df = pd.DataFrame(final_metrics)
    print("\n🌍 SEOUL FULL 3-MODEL RECAP:")
    print(f"Avg CPC (Global P_bin): {results_df['CPC_Global'].mean():.4f}")
    print(f"Avg CPC (No POI):      {results_df['CPC_No_POI'].mean():.4f}")
    print(f"Avg CPC (POI Version):  {results_df['CPC_POI'].mean():.4f}")
    
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"💾 Full comparison metrics saved to {OUTPUT_FILE}.")

if __name__ == "__main__":
    main()
