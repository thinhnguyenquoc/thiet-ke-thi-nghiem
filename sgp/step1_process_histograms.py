import pandas as pd
import numpy as np
import os

# Configuration
TRIPS_FILE = '../test-probability-distribution/data_trip_sum.csv'
DIST_FILE = '../test-probability-distribution/zone_euclid_distances.csv'
OUTPUT_FILE = 'binned_trips_by_zone.csv'

def main():
    print("🚀 Step 1: Processing distance histograms...")
    
    if not os.path.exists(TRIPS_FILE) or not os.path.exists(DIST_FILE):
        print(f"❌ Error: Required data files not found in '../test-probability-distribution/'.")
        return

    # 1. Load data
    print("📖 Loading trips and distances...")
    trips_df = pd.read_csv(TRIPS_FILE)
    dist_df = pd.read_csv(DIST_FILE)
    
    # 2. Merge data to get distances for each trip
    print("🔗 Merging trips with Euclidean distances...")
    merged = pd.merge(trips_df, dist_df, on=['ORIGIN_SUBZONE', 'DESTINATION_SUBZONE'])
    
    # 3. Bin distances into 1km intervals
    print("🧮 Binning distances at 1km intervals...")
    merged['distance_bin'] = np.floor(merged['euclidean_distance_km']).astype(float)
    
    # 4. Aggregate counts per origin and dist_bin
    print("📊 Aggregating histogram data...")
    binned = merged.groupby(['ORIGIN_SUBZONE', 'distance_bin'])['COUNT'].sum().reset_index()
    
    # 5. Save results
    print(f"💾 Saving binned data to {OUTPUT_FILE}...")
    binned.to_csv(OUTPUT_FILE, index=False)
    print("✅ Step 1 complete.")

if __name__ == "__main__":
    main()
