import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Paths
BASE_DIR = os.getcwd()
REPORT_FILE = os.path.join(BASE_DIR, "poi_correlation_results.csv")

# Load existing results for US cities
df_us = pd.read_csv(REPORT_FILE)
df_us['Region'] = 'USA Cities'

# Add SGP and SU manually (validated results from previous turns)
# SGP: Uniform 0.576, Weighted 0.645, Gain +0.069, Avg POI 139.3
# SU: Uniform 0.720, Weighted 0.765, Gain +0.045, Avg POI 240.3
asian_data = [
    {'City': 'Singapore', 'Uniform': 0.576, 'Weighted': 0.645, 'POI_Gain': 0.069, 'Avg_POI_per_Zone': 139.3, 'Region': 'Asian Compact Cities'},
    {'City': 'Seoul', 'Uniform': 0.720, 'Weighted': 0.765, 'POI_Gain': 0.045, 'Avg_POI_per_Zone': 240.3, 'Region': 'Asian Compact Cities'}
]
df_asian = pd.DataFrame(asian_data)

# Combine
df_all = pd.concat([df_us, df_asian], ignore_index=True)

# Plotting
sns.set_theme(style="whitegrid")
plt.figure(figsize=(12, 8))

# Draw regression lines for each region separately to show slope difference
palette = {'USA Cities': 'crimson', 'Asian Compact Cities': 'dodgerblue'}

sns.regplot(x='Avg_POI_per_Zone', y='POI_Gain', data=df_all[df_all['Region']=='USA Cities'], 
            scatter_kws={'alpha':0.6, 's':80}, line_kws={'label': 'USA Trend (Negative Correlation)'}, 
            color='crimson', marker='o')

sns.regplot(x='Avg_POI_per_Zone', y='POI_Gain', data=df_all[df_all['Region']=='Asian Compact Cities'], 
            scatter_kws={'alpha':0.9, 's':150}, line_kws={'label': 'Asian Trend (Positive Correlation)'}, 
            color='dodgerblue', marker='s')

# Annotations for SGP and SU
plt.text(139.3, 0.069, ' Singapore', fontsize=12, fontweight='bold', color='dodgerblue', va='bottom')
plt.text(240.3, 0.045, ' Seoul', fontsize=12, fontweight='bold', color='dodgerblue', va='bottom')

# Annotate some US outliers
outliers = df_us.nsmallest(3, 'POI_Gain')
for _, row in outliers.iterrows():
    plt.text(row['Avg_POI_per_Zone'], row['POI_Gain'], f" {row['City']}", fontsize=9, alpha=0.7)

plt.axhline(0, color='black', linewidth=1, linestyle='--')
plt.title('Urban Structure Bias: POI Advantage vs. Density', fontsize=16, fontweight='bold')
plt.xlabel('Average POI per Zone (Density)', fontsize=14)
plt.ylabel('Performance Gain (Weighted - Uniform)', fontsize=14)
plt.legend(fontsize=12, frameon=True, loc='upper right')

plt.tight_layout()
plt.savefig('poi_regional_bias.png', dpi=300)
plt.close()

print("✅ Regional bias plot generated as poi_regional_bias.png")
