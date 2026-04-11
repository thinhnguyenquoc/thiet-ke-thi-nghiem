import pandas as pd
import numpy as np
import os

# Configuration
ACTUAL_FILE = 'aggregated_trips.csv'
PRED_FILE = 'step3_gravity_results.csv'
OUTPUT_FILE = 'step6_evaluation_results.csv'

def calculate_cpc(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    if total == 0: return 0
    return 2 * intersection / total

def main():
    print("🚀 Step 6 (SEOUL Evaluation): Evaluating Baseline No POI Model...")

    if not os.path.exists(ACTUAL_FILE) or not os.path.exists(PRED_FILE):
        print(f"❌ Error: Required data files missing.")
        return

    # 1. Load Data
    print("📖 Loading actual and predicted flows (this may take a moment)...")
    actual_df = pd.read_csv(ACTUAL_FILE)
    actual_df['ORIGIN_SUBZONE'] = actual_df['ORIGIN_SUBZONE'].astype(float)
    actual_df['DESTINATION_SUBZONE'] = actual_df['DESTINATION_SUBZONE'].astype(float)
    
    pred_df = pd.read_csv(PRED_FILE)
    pred_df['ORIGIN_ZONE'] = pred_df['ORIGIN_ZONE'].astype(float)
    pred_df['DEST_SUBZONE'] = pred_df['DEST_SUBZONE'].astype(float)
    
    unique_origins = pred_df['ORIGIN_ZONE'].unique()
    print(f"📊 Ready to evaluate {len(unique_origins)} origin zones.")

    eval_results = []

    # 2. Iterate and evaluate per origin zone
    for i, origin in enumerate(unique_origins):
        if i % 50 == 0:
            print(f"🕵️ Progress: {i}/{len(unique_origins)}...")
        
        # Ground Truth for this origin
        actual_origin = actual_df[actual_df['ORIGIN_SUBZONE'] == origin][['DESTINATION_SUBZONE', 'COUNT']]
        actual_origin.rename(columns={'COUNT': 'ACTUAL_FLOW'}, inplace=True)
        
        # Model for this origin
        pred_origin = pred_df[pred_df['ORIGIN_ZONE'] == origin][['DEST_SUBZONE', 'T_hat_ij']]
        
        # Align datasets
        merged = pd.merge(pred_origin, actual_origin, left_on='DEST_SUBZONE', right_on='DESTINATION_SUBZONE', how='outer').fillna(0)
        
        y_true = merged['ACTUAL_FLOW'].values
        y_pred = merged['T_hat_ij'].values
        
        # Metrics
        cpc = calculate_cpc(y_true, y_pred)
        # R2 manually
        ss_res = np.sum((y_true - y_pred)**2)
        ss_tot = np.sum((y_true - np.mean(y_true))**2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred)**2))
        
        eval_results.append({
            'Zone': origin,
            'CPC': cpc,
            'R2': r2,
            'MAE': mae,
            'RMSE': rmse,
            'Total_Actual': np.sum(y_true)
        })

    # 3. Save Overall Summary
    summary_df = pd.DataFrame(eval_results)
    avg_cpc = summary_df['CPC'].mean()
    avg_r2 = summary_df['R2'].mean()
    print(f"\n🌍 SEOUL BASELINE (No POI) PERFORMANCE:")
    print(f"Average CPC: {avg_cpc:.4f}")
    print(f"Average R2:  {avg_r2:.4f}")
    
    summary_df.to_csv(OUTPUT_FILE, index=False)
    print(f"💾 Step 6 results saved to {OUTPUT_FILE}.")

if __name__ == "__main__":
    main()
