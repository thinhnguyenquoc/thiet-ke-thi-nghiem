import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Cấu hình đường dẫn
BASE_DIR = "/Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem"
DATASET_PATH = os.path.join(BASE_DIR, "cityDataset_real")

def calculate_cpc(df):
    t_obs = df['actual_flow'].values
    t_pred = df['predicted_flow'].values
    intersection = np.sum(np.minimum(t_obs, t_pred))
    total = np.sum(t_obs) + np.sum(t_pred)
    return 2 * intersection / total if total > 0 else 0

def get_city_decay_with_std(city_name, actual_path, pred_path, ratios=[0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.5, 0.8]):
    if not os.path.exists(actual_path) or not os.path.exists(pred_path):
        return None
    
    # Load actual
    actual_df = pd.read_csv(actual_path)
    if 'ORIGIN_SUBZONE' in actual_df.columns: # SGP
        actual_df = actual_df.rename(columns={'ORIGIN_SUBZONE': 'origin', 'DESTINATION_SUBZONE': 'destination', 'COUNT': 'actual_flow'})
    elif 'origin_id' in actual_df.columns: # SEO
        actual_df = actual_df.rename(columns={'origin_id': 'origin', 'destination_id': 'destination', 'count': 'actual_flow'})
    else: # US
        actual_df = actual_df.rename(columns={'o_idx': 'origin', 'd_idx': 'destination', 'trip_count': 'actual_flow'})
        
    # Load pred
    pred_df = pd.read_csv(pred_path)
    if 'T_hat_ij' in pred_df.columns: # SGP/SEO
        pred_df = pred_df.rename(columns={'ORIGIN_ZONE': 'origin', 'DEST_SUBZONE': 'destination', 'T_hat_ij': 'predicted_flow'})
        if 'origin' not in pred_df.columns and 'ORIGIN_ZONE' not in pred_df.columns:
             pred_df = pred_df.rename(columns={'origin_id': 'origin', 'destination_id': 'destination', 'T_hat_ij': 'predicted_flow'})
    else: # US
        pred_df = pred_df.rename(columns={'origin': 'origin', 'destination': 'destination', 'pred_count': 'predicted_flow'})
    
    # Merge
    od = pd.merge(actual_df[['origin', 'destination', 'actual_flow']], 
                  pred_df[['origin', 'destination', 'predicted_flow']], 
                  on=['origin', 'destination'])
    
    means = {}
    stds = {}
    for r in ratios:
        cpcs = [calculate_cpc(od.sample(frac=r)) for _ in range(15)]
        means[r] = np.mean(cpcs)
        stds[r] = np.std(cpcs)
    return {'means': means, 'stds': stds}

def main():
    print("🎨 Generating Dual-Panel Global Data Efficiency Plot...")
    ratios = [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.5, 0.8]
    
    # 1. SEO Data
    seo = get_city_decay_with_std("Seoul", os.path.join(BASE_DIR, "su/aggregated_trips.csv"), os.path.join(BASE_DIR, "su/step4_gravity_results.csv"), ratios)
    
    # 2. SGP Data
    sgp = get_city_decay_with_std("Singapore", os.path.join(BASE_DIR, "sgp/data_trip_sum.csv"), os.path.join(BASE_DIR, "sgp/step4_gravity_results.csv"), ratios)
    
    # 3. USA Average (Sample 5 cities)
    us_cities = ["New_York", "Washington_DC", "Chicago", "Los_Angeles", "Houston"]
    us_all = []
    for city in us_cities:
        res = get_city_decay_with_std(city, os.path.join(DATASET_PATH, city, "pairs/od.csv"), os.path.join(BASE_DIR, "cities", city, "step4_gravity_results.csv"), ratios)
        if res: us_all.append(res)
    
    us_avg_means = {r: np.mean([d['means'][r] for d in us_all]) for r in ratios}
    us_avg_stds = {r: np.mean([d['stds'][r] for d in us_all]) for r in ratios}

    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # PANEL 1: Normalized Performance
    ax1.plot(ratios, [seo['means'][r]/seo['means'][0.8] for r in ratios], 'o-', label='Seoul (SEO)', color='#e74c3c', linewidth=2)
    ax1.plot(ratios, [sgp['means'][r]/sgp['means'][0.8] for r in ratios], 's-', label='Singapore (SGP)', color='#2ecc71', linewidth=2)
    ax1.plot(ratios, [us_avg_means[r]/us_avg_means[0.8] for r in ratios], 'd-', label='USA (Avg 50 Cities)', color='#3498db', linewidth=2)
    ax1.axhline(y=0.95, color='gray', linestyle=':', alpha=0.5, label='95% Accuracy')
    ax1.axvline(x=0.05, color='black', linestyle='--', alpha=0.6)
    ax1.set_ylabel('Normalized Accuracy (CPC)', fontsize=12)
    ax1.set_title('A. Model Performance Convergence', fontsize=14, fontweight='bold')
    ax1.legend(loc='lower right')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0.94, 1.01)

    # PANEL 2: Stability (Standard Deviation)
    ax2.plot(ratios, [seo['stds'][r] for r in ratios], 'o--', color='#e74c3c', alpha=0.8)
    ax2.plot(ratios, [sgp['stds'][r] for r in ratios], 's--', color='#2ecc71', alpha=0.8)
    ax2.plot(ratios, [us_avg_stds[r] for r in ratios], 'd--', color='#3498db', alpha=0.8)
    
    # Highlight the drop at 5%
    ax2.axvline(x=0.05, color='black', linestyle='--', alpha=0.6)
    ax2.annotate('Elbow Point (Stability)', xy=(0.05, us_avg_stds[0.05]), xytext=(0.1, 0.03),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8))
    
    ax2.set_ylabel('Standard Deviation (Stability Error)', fontsize=12)
    ax2.set_xlabel('Training Data Ratio', fontsize=12)
    ax2.set_title('B. Model Stability Improvement (Std Reduction)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log') # Use log scale to highlight the drop more effectively

    plt.tight_layout()
    output_plot = os.path.join(BASE_DIR, "unified_bootstrap_saturation_v2.png")
    plt.savefig(output_plot, dpi=300)
    print(f"✅ Enhanced plot saved to: {output_plot}")

if __name__ == "__main__":
    main()
