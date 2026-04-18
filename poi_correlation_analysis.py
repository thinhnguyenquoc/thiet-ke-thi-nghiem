import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Paths
BASE_DIR = os.getcwd()
DATA_DIR_ROOT = os.path.join(BASE_DIR, "cityDataset_real")
REPORT_FILE = os.path.join(BASE_DIR, "FINAL_ALL_CITIES_REPORT.csv")

def get_poi_stats(city):
    p_file = os.path.join(DATA_DIR_ROOT, city, "nodes/poi.csv")
    if os.path.exists(p_file):
        df_p = pd.read_csv(p_file)
        return {
            'City': city,
            'Total_POI': df_p['total_pois'].sum(),
            'Avg_POI_per_Zone': df_p['total_pois'].mean(),
            'Max_POI': df_p['total_pois'].max()
        }
    return None

def analyze():
    # Load report
    all_metrics = pd.read_csv(REPORT_FILE)
    
    # Filter for Shell models
    shell_results = all_metrics[all_metrics['Model'].isin(['Uniform', 'Weighted'])]
    pivot_results = shell_results.pivot(index='City', columns='Model', values='CPC').reset_index()
    pivot_results['POI_Gain'] = pivot_results['Weighted'] - pivot_results['Uniform']
    
    # Collect POI stats
    cities = pivot_results['City'].unique()
    poi_data = []
    for c in cities:
        stats = get_poi_stats(c)
        if stats: poi_data.append(stats)
    
    poi_df = pd.DataFrame(poi_data)
    
    # Merge
    merged = pd.merge(pivot_results, poi_df, on='City')
    
    # Correlation Analysis
    corr_total = merged['POI_Gain'].corr(merged['Total_POI'])
    corr_density = merged['POI_Gain'].corr(merged['Avg_POI_per_Zone'])
    
    print(f"📊 Tracking POI Density vs Weighted Model Performance:")
    print(f"- Correlation (Gain vs Total POI): {corr_total:.3f}")
    print(f"- Correlation (Gain vs Avg POI per Zone): {corr_density:.3f}")
    
    # Plotting
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    sns.regplot(x='Avg_POI_per_Zone', y='POI_Gain', data=merged, color='teal')
    plt.title('Correlation between POI Density and Weighted Model Advantage', fontsize=14, fontweight='bold')
    plt.xlabel('Average POI per Zone (Density Proxy)', fontsize=12)
    plt.ylabel('Performance Gain (Weighted - Uniform)', fontsize=12)
    
    # Annotate key cities
    top_gain = merged.nlargest(5, 'POI_Gain')
    for _, row in top_gain.iterrows():
        plt.text(row['Avg_POI_per_Zone'], row['POI_Gain'], f" {row['City']}", fontsize=9, va='bottom')

    plt.tight_layout()
    plt.savefig('poi_density_correlation.png', dpi=300)
    
    merged.to_csv("poi_correlation_results.csv", index=False)
    print("\n✅ Correlation analysis done. Plot saved as poi_density_correlation.png")

if __name__ == "__main__":
    analyze()
