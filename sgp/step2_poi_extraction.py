import pandas as pd
import geopandas as gpd
import os

# Configuration
POI_GEOJSON = 'detail_pois.geojson'
SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
OUTPUT_CSV = 'pois_by_zone.csv'

def main():
    print("🚀 Extracting POI counts from GeoJSON (summary format)...")
    
    if not os.path.exists(POI_GEOJSON):
        print(f"❌ Error: {POI_GEOJSON} not found.")
        return

    # 1. Load Geometries to get all subzones
    print("📖 Loading shapefile...")
    gdf_sz = gpd.read_file(SZ_SHAPEFILE)
    gdf_sz['SUBZONE_C'] = gdf_sz['SUBZONE_C'].astype(str).str.strip().str.upper()
    
    # 2. Load POIs
    print("📖 Loading POI GeoJSON...")
    gdf_poi = gpd.read_file(POI_GEOJSON)
    gdf_poi['SUBZONE_C'] = gdf_poi['SUBZONE_C'].astype(str).str.strip().str.upper()
    
    # Identity POI columns (amenity, shop, etc.)
    poi_cols = ['amenity', 'shop', 'tourism', 'leisure', 'office', 'public_transport']
    existing_cols = [c for c in poi_cols if c in gdf_poi.columns]
    print(f"🔍 Summing POI columns: {existing_cols}")
    
    # 3. Sum the columns
    gdf_poi['A_j_total'] = gdf_poi[existing_cols].sum(axis=1)
    
    # 4. Aggregate (in case there are multiple rows per zone, but here 1 row per zone)
    poi_counts = gdf_poi.groupby('SUBZONE_C')['A_j_total'].sum().reset_index(name='A_j')
    
    # 5. Merge back to all subzones to ensure coverage
    all_zones = gdf_sz[['SUBZONE_C']].copy()
    final_df = pd.merge(all_zones, poi_counts, on='SUBZONE_C', how='left').fillna(0)
    
    print(f"💾 Saving {len(final_df)} zones to {OUTPUT_CSV}...")
    final_df.to_csv(OUTPUT_CSV, index=False)
    
    total_pois = final_df['A_j'].sum()
    print(f"✅ Extraction complete. Total POIs mapped: {total_pois}")
    print(final_df.head())

if __name__ == "__main__":
    main()
