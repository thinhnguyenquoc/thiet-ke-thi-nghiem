import pandas as pd
import geopandas as gpd
import numpy as np
import os

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
TRIPS_FILE = 'data_trip_sum.csv'
OUTPUT_FILE = 'binned_trips_by_zone.csv'
CITY_CRS = 'EPSG:3414' # SVY21 for Singapore

def main():
    print("🚀 Step 1: Processing distance histograms from Shapefile...")
    
    if not os.path.exists(SZ_SHAPEFILE) or not os.path.exists(TRIPS_FILE):
        print(f"❌ Error: Required data files not found in local directory.")
        return

    # 1. Load geometries and calculate distances
    print("📖 Loading subzone geometries...")
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(str).str.strip().str.upper()
    
    # Calculate centroids in projected CRS
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    print("📏 Calculating distance matrix...")
    unique_zones = gdf_utm['SUBZONE_C'].unique()
    zone_coords = gdf_utm.set_index('SUBZONE_C')['centroid']
    
    # 2. Load trips
    print("📖 Loading trips...")
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(str).str.strip().str.upper()
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(str).str.strip().str.upper()
    
    # Filter trips to only include zones in our shapefile AND exclude internal flows (j != i)
    print("✂️ Excluding internal flows (i -> i) and filtering by shapefile...")
    trips_df = trips_df[
        (trips_df['ORIGIN_SUBZONE'].isin(unique_zones)) & 
        (trips_df['DESTINATION_SUBZONE'].isin(unique_zones)) &
        (trips_df['ORIGIN_SUBZONE'] != trips_df['DESTINATION_SUBZONE'])
    ]

    # Calculate distances for the trips present
    print("🔗 Computing Euclidean distances for observed trips...")
    def get_dist(row):
        p1 = zone_coords[row['ORIGIN_SUBZONE']]
        p2 = zone_coords[row['DESTINATION_SUBZONE']]
        return p1.distance(p2) / 1000.0

    # For large datasets, vectorized approach with merge is faster
    # Create distance lookup
    dist_list = []
    # Only compute distances for zones that actually have trips between them to save time
    # or just pre-calculate all pairs if feasible (SGP has ~300 zones, 300^2 = 90k pairs, feasible)
    
    all_pairs_dist = []
    coords_vals = np.array([[p.x, p.y] for p in zone_coords])
    dist_matrix = np.sqrt(np.sum((coords_vals[:, np.newaxis, :] - coords_vals[np.newaxis, :, :])**2, axis=2)) / 1000.0
    
    dist_lookup = pd.DataFrame(dist_matrix, index=unique_zones, columns=unique_zones).stack().reset_index()
    dist_lookup.columns = ['ORIGIN_SUBZONE', 'DESTINATION_SUBZONE', 'euclidean_distance_km']
    
    # 3. Merge and Bin
    print("🧮 Binning distances at 1km intervals...")
    merged = pd.merge(trips_df, dist_lookup, on=['ORIGIN_SUBZONE', 'DESTINATION_SUBZONE'])
    merged['distance_bin'] = np.floor(merged['euclidean_distance_km']).astype(float)
    
    # 4. Aggregate counts per origin and dist_bin
    print("📊 Aggregating histogram data...")
    binned = merged.groupby(['ORIGIN_SUBZONE', 'distance_bin'])['COUNT'].sum().reset_index()
    
    # 5. Save results
    print(f"💾 Saving binned data to {OUTPUT_FILE}...")
    binned.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Step 1 complete. Total bins generated: {len(binned)}")

if __name__ == "__main__":
    main()
