import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# Load data
sgp = pd.read_csv("sgp/step8_partial_training_results.csv")
su = pd.read_csv("su/step10_partial_training_results.csv")
us = pd.read_csv("us_partial_training_avg.csv")

# Plotting
plt.figure(figsize=(12, 7))

# Plot each city/region
plt.plot(sgp['Ratio'] * 100, sgp['CPC'], 'o-', label='Singapore (SGP)', linewidth=2.5, markersize=8)
plt.plot(su['Ratio'] * 100, su['CPC'], 's-', label='Seoul (SU)', linewidth=2.5, markersize=8)
plt.plot(us['Ratio'] * 100, us['CPC'], 'd-', label='USA Cities (Avg of 10)', linewidth=3, markersize=10, color='crimson')

# Add 10% threshold line
plt.axvline(x=10, color='gray', linestyle='--', alpha=0.7)
plt.text(10.5, plt.ylim()[0] + 0.02, '10% Data Saturation', color='gray', fontweight='bold')

# Formatting
plt.title('Ổn định không gian của quy luật Shell qua các quy mô dữ liệu mẫu', fontsize=18, fontweight='bold')
plt.xlabel('Tỷ lệ dữ liệu mẫu (%)', fontsize=14)
plt.ylabel('Origin-Averaged CPC', fontsize=14)
plt.legend(fontsize=12, frameon=True, shadow=True)
plt.grid(True, which='both', linestyle='--', alpha=0.5)

# Annotate saturation points
for df, label in zip([sgp, su, us], ['SGP', 'SU', 'USA']):
    ratio_10 = df.iloc[-1] # assuming last raw is ~10%
    plt.annotate(f"{ratio_10['CPC']:.3f}", 
                 xy=(ratio_10['Ratio']*100, ratio_10['CPC']),
                 xytext=(5, 5), textcoords='offset points',
                 fontweight='bold')

plt.tight_layout()
plt.savefig('unified_partial_training.png', dpi=300)
plt.close()

print("✅ Unified partial training plot generated as unified_partial_training.png")
