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

# Add SGP and SU manually
asian_data = [
    {'City': 'Singapore', 'Uniform': 0.576, 'Weighted': 0.645, 'POI_Gain': 0.069, 'Avg_POI_per_Zone': 139.3, 'Region': 'Asian Compact Cities'},
    {'City': 'Seoul', 'Uniform': 0.720, 'Weighted': 0.765, 'POI_Gain': 0.045, 'Avg_POI_per_Zone': 240.3, 'Region': 'Asian Compact Cities'}
]
df_asian = pd.DataFrame(asian_data)

# Combine
df_all = pd.concat([df_us, df_asian], ignore_index=True)

# Define Color based on POI_Gain (Positive = Blue, Negative = Red)
df_all['Color_Group'] = np.where(df_all['POI_Gain'] > 0, 'Positive Correlation (Weighted Advantage)', 'Negative Correlation (Uniform Advantage)')

# Plotting
sns.set_theme(style="whitegrid")
plt.figure(figsize=(12, 8))

# Palette matching user request
palette = {'Positive Correlation (Weighted Advantage)': 'dodgerblue', 
           'Negative Correlation (Uniform Advantage)': 'crimson'}

# Scatter plot with colors based on correlation direction
sns.scatterplot(x='Avg_POI_per_Zone', y='POI_Gain', hue='Color_Group', data=df_all, 
                palette=palette, s=120, alpha=0.8, edgecolor='w', linewidth=1)

# Regression lines to show the trend
sns.regplot(x='Avg_POI_per_Zone', y='POI_Gain', data=df_all[df_all['POI_Gain'] > 0], 
            scatter=False, color='dodgerblue', line_kws={'linestyle': '--', 'alpha': 0.5})
sns.regplot(x='Avg_POI_per_Zone', y='POI_Gain', data=df_all[df_all['POI_Gain'] <= 0], 
            scatter=False, color='crimson', line_kws={'linestyle': '--', 'alpha': 0.5})

# Annotations for SGP and SU
plt.text(139.3, 0.069, ' Singapore', fontsize=12, fontweight='bold', color='navy', va='bottom')
plt.text(240.3, 0.045, ' Seoul', fontsize=12, fontweight='bold', color='navy', va='bottom')

# Annotate key US cities with positive gain
pos_us = df_us[df_us['POI_Gain'] > 0.03].sort_values('Avg_POI_per_Zone')
for _, row in pos_us.iterrows():
    plt.text(row['Avg_POI_per_Zone'], row['POI_Gain'], f" {row['City']}", fontsize=10, color='dodgerblue')

plt.axhline(0, color='black', linewidth=1.5, linestyle='-')
plt.title('Phân loại hiệu quả của POI theo đặc trưng đô thị (POI Gain vs. Density)', fontsize=16, fontweight='bold')
plt.xlabel('Average POI per Zone (Mật độ tiện ích)', fontsize=14)
plt.ylabel('Performance Gain (Weighted - Uniform)', fontsize=14)
plt.legend(title='Correlation Group', fontsize=11, title_fontsize=12, frameon=True, shadow=True)

plt.tight_layout()
plt.savefig('poi_regional_bias.png', dpi=300)
plt.close()

print("✅ Updated plot with positive correlation points in blue.")
