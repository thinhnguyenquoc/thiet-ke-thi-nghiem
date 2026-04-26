import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def calculate_cpc(df):
    """
    Tính toán độ đo CPC (Common Part of Commuters)
    Công thức: 2 * sum(min(T_obs, T_pred)) / (sum(T_obs) + sum(T_pred))
    """
    t_obs = df['actual_flow'].values
    t_pred = df['predicted_flow'].values
    intersection = np.sum(np.minimum(t_obs, t_pred))
    total = np.sum(t_obs) + np.sum(t_pred)
    return 2 * intersection / total if total > 0 else 0

def bootstrap_analysis(OD_matrix, ratios=[0.05, 0.1, 0.2, 0.5, 0.8], n_iterations=20):
    """
    Hàm bootstrap_analysis:
    - Input: DataFrame OD_matrix, danh sách tỷ lệ.
    - Cách làm: Mỗi tỷ lệ chạy 20 lần. Mỗi lần lấy mẫu ngẫu nhiên theo số lượng bản ghi (rows).
    """
    results = {}
    print(f"📊 Starting Bootstrap Analysis with ratios: {ratios}")
    
    for r in ratios:
        cpc_list = []
        for i in range(n_iterations):
            # Lấy mẫu ngẫu nhiên theo số lượng bản ghi (rows)
            sample_df = OD_matrix.sample(frac=r, replace=False)
            cpc_val = calculate_cpc(sample_df)
            cpc_list.append(cpc_val)
        
        results[r] = {
            'mean': np.mean(cpc_list),
            'std': np.std(cpc_list)
        }
        print(f"   - Ratio {r*100:>3.0f}%: Mean CPC = {results[r]['mean']:.4f}, Std = {results[r]['std']:.4f}")
    
    return results

def main():
    print("🚀 Step 8: Data Efficiency Bootstrap Analysis (Improved Shell Model)")
    
    # 1. Load and Prepare Data
    ACTUAL_FILE = 'aggregated_trips.csv'
    PRED_FILE = 'step4_gravity_results.csv' # Shell Weighted Model
    
    if not os.path.exists(ACTUAL_FILE) or not os.path.exists(PRED_FILE):
        print("❌ Error: Missing data files.")
        return

    # Load actual
    actual_df = pd.read_csv(ACTUAL_FILE)
    actual_df['origin'] = actual_df['ORIGIN_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    actual_df['destination'] = actual_df['DESTINATION_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    actual_df = actual_df[['origin', 'destination', 'COUNT']].rename(columns={'COUNT': 'actual_flow'})
    
    # Load predicted
    pred_df = pd.read_csv(PRED_FILE)
    pred_df['origin'] = pred_df['ORIGIN_ZONE'].astype(str).str.replace('.0', '', regex=False)
    pred_df['destination'] = pred_df['DEST_SUBZONE'].astype(str).str.replace('.0', '', regex=False)
    pred_df = pred_df[['origin', 'destination', 'T_hat_ij']].rename(columns={'T_hat_ij': 'predicted_flow'})
    
    # Merge to get the required structure
    # We use inner join to ensure we have both values for each OD pair
    od_matrix = pd.merge(actual_df, pred_df, on=['origin', 'destination'], how='inner')
    
    print(f"✅ Data merged. Total OD records: {len(od_matrix)}")
    
    # 2. Run Bootstrap
    ratios = [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.5, 0.8]
    bootstrap_results = bootstrap_analysis(od_matrix, ratios)

    
    # 3. Reference: 100% Data CPC
    max_cpc = calculate_cpc(od_matrix)
    print(f"📈 Maximum CPC (100% data): {max_cpc:.4f}")
    
    # 4. Visualization
    r_list = sorted(bootstrap_results.keys())
    means = [bootstrap_results[r]['mean'] for r in r_list]
    stds = [bootstrap_results[r]['std'] for r in r_list]
    
    plt.figure(figsize=(10, 6))
    
    # Plot mean CPC
    plt.plot(r_list, means, marker='o', label='Mean CPC', color='#1f77b4', linewidth=2)
    
    # Plot shaded area (std)
    plt.fill_between(r_list, 
                     np.array(means) - np.array(stds), 
                     np.array(means) + np.array(stds), 
                     alpha=0.2, color='#1f77b4', label='Standard Deviation')
    
    # Plot 100% Max line
    plt.axhline(y=max_cpc, color='r', linestyle='--', label='100% Data CPC')
    
    # Plot 95% threshold line
    target_95 = 0.95 * max_cpc
    plt.axhline(y=target_95, color='g', linestyle=':', label='95% Threshold')
    
    # Find saturation point (95% of max)
    saturation_point = None
    for r in r_list:
        if bootstrap_results[r]['mean'] >= target_95:
            saturation_point = r
            break
            
    if saturation_point:
        print(f"🎯 95% of maximum CPC is reached at {saturation_point*100:.0f}% data.")
        plt.annotate(f'95% Max reached at {saturation_point*100:.0f}% data',
                     xy=(saturation_point, bootstrap_results[saturation_point]['mean']),
                     xytext=(saturation_point + 0.05, bootstrap_results[saturation_point]['mean'] - 0.05),
                     arrowprops=dict(facecolor='black', shrink=0.05))
    else:
        print("⚠️ 95% of maximum CPC not reached in the selected ratios.")
    
    plt.title('Improved Shell Model Decay Analysis: CPC vs. Training Data Ratio', fontsize=14)
    plt.xlabel('Training Data Fraction (Ratio)', fontsize=12)
    plt.ylabel('Common Part of Commuters (CPC)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save the plot
    output_plot = 'step10_bootstrap_cpc_decay.png'
    plt.savefig(output_plot, dpi=300)
    print(f"🖼️ Plot saved to: {output_plot}")
    
    # 5. Analysis Result Display
    print("\n📝 Final Analysis:")
    print(f"   - Max CPC (100%): {max_cpc:.4f}")
    print(f"   - 95% Target: {target_95:.4f}")
    if saturation_point:
        print(f"   - Saturation Point: {saturation_point*100}% data is sufficient to reach 95% performance.")
    else:
        print(f"   - Saturation Point: More than 80% data may be needed.")

if __name__ == "__main__":
    main()
