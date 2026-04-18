import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.manifold import MDS
import subprocess

# Paths
BASE_DIR = os.getcwd()
DATA_DIR_ROOT = os.path.join(BASE_DIR, "cityDataset_real")
OUTPUT_DIR_ROOT = os.path.join(BASE_DIR, "cities")

# Sample cities to speed up
CITIES_TO_ANALYZE = ['Albuquerque', 'Arlington', 'Atlanta', 'Austin', 'Baltimore', 
                     'Boston', 'Charlotte', 'Chicago', 'Columbus', 'Dallas']

def run_partial_training_for_city(city_name):
    print(f"🔄 Partial Training for {city_name}...")
    city_data_dir = os.path.join(DATA_DIR_ROOT, city_name)
    od_file = os.path.join(city_data_dir, "pairs/od.csv")
    dist_file = os.path.join(city_data_dir, "pairs/distance.csv")
    
    if not os.path.exists(od_file): return None
    
    od = pd.read_csv(od_file)
    dist = pd.read_csv(dist_file)
    od.rename(columns={'o_idx': 'origin', 'd_idx': 'destination', 'trip_count': 'count'}, inplace=True)
    dist.rename(columns={'o_idx': 'origin', 'd_idx': 'destination', 'distance_km': 'distance'}, inplace=True)
    
    zones = sorted(dist['origin'].unique())
    Z = len(zones)
    zone_to_idx = {z: i for i, z in enumerate(zones)}
    
    # Distance Matrix for MDS
    dm = np.zeros((Z, Z))
    for _, row in dist.iterrows():
        if row['origin'] in zone_to_idx and row['destination'] in zone_to_idx:
            dm[zone_to_idx[row['origin']], zone_to_idx[row['destination']]] = row['distance']
    
    # Force symmetry for MDS
    dm = (dm + dm.T) / 2.0
    
    # Reconstruct coordinates using MDS
    print(f"  📍 Reconstructing coordinates for {city_name} using MDS...")
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
    coords = mds.fit_transform(dm)
    
    n_values = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    # Diagonal ground truth
    # pivot might fail if some pairs are missing, use idx mapping
    actual_mat = np.zeros((Z, Z))
    for _, row in od.iterrows():
        if row['origin'] in zone_to_idx and row['destination'] in zone_to_idx:
            actual_mat[zone_to_idx[row['origin']], zone_to_idx[row['destination']]] = row['count']
            
    internal_diag = np.diag(actual_mat)
    origin_ext_sums = actual_mat.sum(axis=1) - internal_diag
    
    results = []
    
    for n in n_values:
        n_clusters = Z // n
        if n_clusters < 2: continue
        
        # Clustering on reconstructed coords
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
        clusters = kmeans.fit_predict(coords)
        
        cluster_df = pd.DataFrame({'idx': zones, 'cluster': clusters})
        
        cpcs = []
        for seed in range(5):
            np.random.seed(seed)
            selected_origins = cluster_df.groupby('cluster')['idx'].apply(lambda x: np.random.choice(x.values)).values
            
            # Predict
            sub_od = od[od['origin'].isin(selected_origins) & (od['origin'] != od['destination'])]
            sub_od = pd.merge(sub_od, dist, on=['origin', 'destination'])
            sub_od['bin'] = np.floor(sub_od['distance']).astype(int)
            
            p_bin = sub_od.groupby('bin')['count'].sum() / (sub_od['count'].sum() + 1e-9)
            
            pred_mat = np.zeros((Z, Z))
            for i, origin in enumerate(zones):
                o_out = origin_ext_sums[i]
                if o_out == 0: continue
                
                dists = dm[i]
                bins = np.floor(dists).astype(int)
                
                for b, prob in p_bin.items():
                    in_bin = (bins == b) & (np.arange(Z) != i)
                    ws = in_bin.sum()
                    if ws > 0:
                        pred_mat[i, in_bin] += (o_out * prob) / ws
            
            final_pred = pred_mat + np.diag(internal_diag)
            it = np.sum(np.minimum(actual_mat, final_pred))
            tot = np.sum(actual_mat) + np.sum(final_pred)
            cpcs.append(2 * it / tot)
            
        results.append({'Ratio': 1.0/n, 'CPC': np.mean(cpcs)})
        
    return pd.DataFrame(results)

def main():
    all_results = []
    for city in CITIES_TO_ANALYZE:
        try:
            res = run_partial_training_for_city(city)
            if res is not None:
                res['City'] = city
                all_results.append(res)
        except Exception as e:
            print(f"❌ Error in {city}: {e}")
            
    if all_results:
        master_df = pd.concat(all_results)
        avg_us = master_df.groupby('Ratio')['CPC'].mean().reset_index()
        avg_us.to_csv("us_partial_training_avg.csv", index=False)
        print("✅ US Partial Training analysis done.")

if __name__ == "__main__":
    main()
