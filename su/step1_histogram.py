import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
import os
import matplotlib.pyplot as plt

# Configuration
INPUT_FILE = 'aggregated_trips.csv'
OUTPUT_FILE = 'binned_trips_by_zone.csv'
CITY_CRS = 'EPSG:4326'  # Lat/Long
PROJECTED_CRS = 'EPSG:5179'  # UTM-K (South Korea)

def main():
    print("🚀 Step 1: Processing distance histograms for Seoul...")

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    # 1. Load data
    print("📖 Loading aggregated trips...")
    df = pd.read_csv(INPUT_FILE)
    
    # Filter trips to exclude internal flows (ground truth)
    print("✂️ Excluding internal flows (i -> i)...")
    df = df[df['ORIGIN_SUBZONE'] != df['DESTINATION_SUBZONE']]
    
    # 2. Convert coordinates to standard distance in kilometers
    print("🌍 Projecting coordinates to UTM-K (EPSG:5179)...")
    
    # Origins
    geometry_o = [Point(xy) for xy in zip(df['ORIGIN_SUBZONE_X'], df['ORIGIN_SUBZONE_Y'])]
    gdf_o = gpd.GeoDataFrame(df[['ORIGIN_SUBZONE']], geometry=geometry_o, crs=CITY_CRS)
    gdf_o = gdf_o.to_crs(PROJECTED_CRS)
    
    # Destinations
    geometry_d = [Point(xy) for xy in zip(df['DESTINATION_SUBZONE_X'], df['DESTINATION_SUBZONE_Y'])]
    gdf_d = gpd.GeoDataFrame(df[['DESTINATION_SUBZONE']], geometry=geometry_d, crs=CITY_CRS)
    gdf_d = gdf_d.to_crs(PROJECTED_CRS)
    
    # Calculate distances in km
    print("🧮 Calculating Euclidean distances (km)...")
    df['calculated_distance_km'] = gdf_o.geometry.distance(gdf_d.geometry) / 1000.0
    
    # 3. Bin distances into 1km intervals
    print("📊 Aggregating trips into 1km bins...")
    df['distance_bin'] = np.floor(df['calculated_distance_km']).astype(float)
    
    # Group by origin and bin
    binned = df.groupby(['ORIGIN_SUBZONE', 'distance_bin'])['COUNT'].sum().reset_index()
    
    # 4. Save results
    print(f"💾 Saving binned results to {OUTPUT_FILE}...")
    binned.to_csv(OUTPUT_FILE, index=False)
    
    # 5. Visualization (Optional check for a sample zone)
    sample_zone = binned['ORIGIN_SUBZONE'].iloc[0]
    print(f"📈 Generating sample histogram for Zone {sample_zone}...")
    sample_data = binned[binned['ORIGIN_SUBZONE'] == sample_zone]
    
    plt.figure(figsize=(10, 6))
    plt.bar(sample_data['distance_bin'], sample_data['COUNT'], color='skyblue', edgecolor='black')
    plt.title(f'Trip Distance Distribution - SEOUL (Zone {sample_zone})')
    plt.xlabel('Distance Bin (km)')
    plt.ylabel('Trip Volume')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(f'Seoul_Zone_{int(sample_zone)}_histogram.png')
    
    print("✅ Step 1 complete.")

if __name__ == "__main__":
    main()
