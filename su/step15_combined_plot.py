import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FILE13 = os.path.join(CURRENT_DIR, 'step13_subzone_sensitivity_results.csv')
FILE14 = os.path.join(CURRENT_DIR, 'step14_subzone_sensitivity_results.csv')
OUTPUT_PLOT = os.path.join(CURRENT_DIR, 'step15_comprehensive_sensitivity.png')

def main():
    print("📊 Generating Comprehensive Sensitivity Chart...")
    
    # 1. Load data
    df13 = pd.read_csv(FILE13)
    df14 = pd.read_csv(FILE14)
    
    # Merge and sort
    df = pd.concat([df13, df14]).sort_values(by='Ratio')
    df['Percent'] = df['Ratio'] * 100
    
    # 2. Plotting
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Error bars for standard deviation
    ax.errorbar(df['Percent'], df['Avg_CPC'], yerr=df['Std_CPC'], 
                fmt='-o', color='#2c3e50', ecolor='#e74c3c', capsize=3, label='Global Law CPC (Seoul)')
    
    # Labels and Title
    ax.set_xlabel('Percentage of Subzones Used for Training (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Origin-Averaged CPC', fontsize=12, fontweight='bold')
    ax.set_title('Seoul Mobility Law: Sensitivity to Data Scales (1% to 100%)', fontsize=14, fontweight='bold', pad=20)
    
    # Log scale X-axis
    ax.set_xscale('log')
    ax.set_xticks([1, 2, 5, 10, 20, 50, 100])
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    
    # Remove annotations, legends, and baseline as requested
    ax.set_ylim(0.71, 0.74) # Adjusted ylim to focus on the curve range
    
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT, dpi=300)
    print(f"📈 Minimalist comprehensive chart saved to {OUTPUT_PLOT}")

if __name__ == "__main__":
    main()
