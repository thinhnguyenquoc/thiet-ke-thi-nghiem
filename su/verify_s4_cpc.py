import pandas as pd
import numpy as np

def calculate_origin_averaged_cpc(real_df, pred_df):
    unique_origins = real_df['ORIGIN_SUBZONE'].unique()
    cpcs = []
    real_gb = real_df.groupby('ORIGIN_SUBZONE')
    pred_gb = pred_df.groupby('ORIGIN_SUBZONE')
    for origin in unique_origins:
        if origin not in pred_gb.groups:
            continue
        r_z = real_gb.get_group(origin)[['DEST_SUBZONE', 'COUNT']]
        p_z = pred_gb.get_group(origin)[['DEST_SUBZONE', 'T_hat_ij']]
        merged = pd.merge(r_z, p_z, on='DEST_SUBZONE', how='outer').fillna(0)
        y_true = merged['COUNT'].values
        y_pred = merged['T_hat_ij'].values
        intersection = np.sum(np.minimum(y_true, y_pred))
        total = np.sum(y_true) + np.sum(y_pred)
        cpcs.append(2.0 * intersection / total if total > 0 else 0.0)
    return np.mean(cpcs)

real_trips = pd.read_csv('aggregated_trips.csv')[['ORIGIN_SUBZONE', 'DESTINATION_SUBZONE', 'COUNT']]
real_trips.rename(columns={'DESTINATION_SUBZONE': 'DEST_SUBZONE'}, inplace=True)
s4_results = pd.read_csv('step4_gravity_results.csv')
s4_results.rename(columns={'ORIGIN_ZONE': 'ORIGIN_SUBZONE'}, inplace=True)

print(f"S4 Origin-Averaged CPC: {calculate_origin_averaged_cpc(real_trips, s4_results)}")
