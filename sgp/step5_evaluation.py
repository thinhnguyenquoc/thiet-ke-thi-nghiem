import pandas as pd
import numpy as np
import os

# Configuration
ACTUAL_FILE = '../test-probability-distribution/data_trip_sum.csv'
STEP3_FILE = 'step3_gravity_results.csv'
STEP4_FILE = 'step4_gravity_results.csv'
OUTPUT_FILE = 'step5_evaluation_results.csv'

def calculate_cpc(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    if total == 0: return 0
    return 2 * intersection / total

def main():
    print("🚀 Step 5 (Global Evaluation): Comparing models for all detected zones")

    if not all(os.path.exists(f) for f in [ACTUAL_FILE, STEP3_FILE, STEP4_FILE]):
        print("❌ Error: Missing global result files.")
        return

    # Load large datasets
    print("📖 Loading datasets (this may take a moment)...")
    actual_df = pd.read_csv(ACTUAL_FILE)
    actual_df['ORIGIN_SUBZONE'] = actual_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    actual_df['DESTINATION_SUBZONE'] = actual_df['DESTINATION_SUBZONE'].astype(str).str.strip().str.upper()
    
    s3_df = pd.read_csv(STEP3_FILE)
    s4_df = pd.read_csv(STEP4_FILE)
    
    origin_zones = s3_df['ORIGIN_ZONE'].unique()
    print(f"📊 Ready to evaluate {len(origin_zones)} zones.")

    comparisons = []

    for i, zone in enumerate(origin_zones):
        if i % 50 == 0:
            print(f"🕵️ Evaluation progress: {i}/{len(origin_zones)}...")
        
        # Actual for this zone
        actual_zone = actual_df[actual_df['ORIGIN_SUBZONE'] == zone][['DESTINATION_SUBZONE', 'COUNT']]
        actual_zone.rename(columns={'COUNT': 'ACTUAL_FLOW'}, inplace=True)
        
        # Evaluate No POI
        p3 = s3_df[s3_df['ORIGIN_ZONE'] == zone][['DEST_SUBZONE', 'T_hat_ij']]
        m3 = pd.merge(p3, actual_zone, left_on='DEST_SUBZONE', right_on='DESTINATION_SUBZONE', how='outer').fillna(0)
        cpc3 = calculate_cpc(m3['ACTUAL_FLOW'].values, m3['T_hat_ij'].values)
        
        # Evaluate POI
        p4 = s4_df[s4_df['ORIGIN_ZONE'] == zone][['DEST_SUBZONE', 'T_hat_ij']]
        m4 = pd.merge(p4, actual_zone, left_on='DEST_SUBZONE', right_on='DESTINATION_SUBZONE', how='outer').fillna(0)
        cpc4 = calculate_cpc(m4['ACTUAL_FLOW'].values, m4['T_hat_ij'].values)

        comparisons.append({
            'Zone': zone,
            'CPC_No_POI': cpc3,
            'CPC_POI': cpc4,
            'CPC_Improvement': cpc4 - cpc3,
            'Observed_Trips': np.sum(m4['ACTUAL_FLOW'])
        })

    results_df = pd.DataFrame(comparisons)
    
    # Calculate Global Stats
    avg_cpc_no_poi = results_df['CPC_No_POI'].mean()
    avg_cpc_poi = results_df['CPC_POI'].mean()
    global_improvement = avg_cpc_poi - avg_cpc_no_poi
    
    print("\n🌍 GLOBAL PERFORMANCE RECAP:")
    print(f"Avg CPC (No POI): {avg_cpc_no_poi:.4f}")
    print(f"Avg CPC (POI):    {avg_cpc_poi:.4f}")
    print(f"Global Benefit:    {global_improvement:+.4f} ({global_improvement/avg_cpc_no_poi*100:+.1f}%)")
    
    print(f"\n💾 Saving global evaluation results to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    print("✅ Step 5 Global Complete.")

if __name__ == "__main__":
    main()
