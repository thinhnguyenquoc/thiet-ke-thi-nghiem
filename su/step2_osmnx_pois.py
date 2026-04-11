import pandas as pd
import geopandas as gpd
import osmnx as ox
import os

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
OUTPUT_GEOJSON = 'detail_pois.geojson'
OUTPUT_CSV = 'pois_by_zone.csv'

def main():
    print("🚀 Step 2 (SEOUL Study): Extracting POIs using OSMNX (features_from_bbox)...")

    if not os.path.exists(SZ_SHAPEFILE):
        print(f"❌ Error: {SZ_SHAPEFILE} not found.")
        return

    # 1. Load Seoul Subzones and get Bbox
    print("📖 Loading subzone boundaries and calculating bounding box...")
    shape_gdf = gpd.read_file(SZ_SHAPEFILE)
    shape_gdf = shape_gdf.to_crs("EPSG:4326")
    
    # Bbox: [minx, miny, maxx, maxy]
    west, south, east, north = shape_gdf.total_bounds
    print(f"🗺️ Bbox: S:{south:.3f}, N:{north:.3f}, W:{west:.3f}, E:{east:.3f}")
    
    # 2. Define OSM tags
    tags = {
        'amenity': True, 'shop': True, 'tourism': True,
        'leisure': True, 'office': True, 'public_transport': True
    }

    # 3. Download POIs from OSM using bbox (More robust for large areas)
    print("📡 Downloading POIs via OSMNX bbox (this ensures full coverage)...")
    try:
        # Note: osmnx uses north, south, east, west
        all_pois = ox.features_from_bbox(bbox=(west, south, east, north), tags=tags)
    except Exception as e:
        print(f"❌ Error during OSMNX fetch: {e}")
        return

    print(f"✨ Found {len(all_pois)} raw OSM features.")

    # 4. Clean the POI data (Centroids only)
    print("🧹 Converting features to centroids for point-in-polygon assignment...")
    all_pois['geometry'] = all_pois.centroid
    
    # 5. Spatial Join: Link each POI to a Seoul Subzone
    print("📍 Spatial Join: Categorizing POIs into subzones...")
    joined = gpd.sjoin(all_pois, shape_gdf[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
    
    # 6. Accumulate counts per category
    print("📊 Aggregating POI categories per subzone...")
    
    # Identify which columns exist in the result
    available_tags = [t for t in tags.keys() if t in joined.columns]
    
    # For every POI, mark which category it belongs to (one-hot)
    for tag in available_tags:
        joined[f'count_{tag}'] = joined[tag].notna().astype(int)
    
    # Group by Zone
    counts = joined.groupby('SUBZONE_C')[[f'count_{t}' for t in available_tags]].sum().reset_index()
    counts.rename(columns={f'count_{t}': t for t in available_tags}, inplace=True)
    
    # 7. Merge counts back to the subzone list (all 421 zones)
    # This ensures EVERY zone is present, even if it has 0 POIs
    final_df = shape_gdf[['SUBZONE_C']].merge(counts, on='SUBZONE_C', how='left').fillna(0)
    
    # Attraction Scoring with Laplace Smoothing (+1)
    # This ensures that zones with no OSM data still have a minimum baseline attraction
    final_df['A_j_raw'] = final_df[available_tags].sum(axis=1)
    final_df['A_j'] = final_df['A_j_raw'] + 1.0 
    
    print(f"📈 Total linked POIs: {int(final_df['A_j_raw'].sum())}")
    print(f"📉 Density check: {len(final_df[final_df['A_j_raw'] > 0])}/{len(final_df)} subzones have OSM POIs.")

    # 8. Save results
    print(f"💾 Saving outputs (CSV and GeoJSON)...")
    # Add geometry back for GeoJSON
    final_gdf_spatial = shape_gdf.merge(final_df, on='SUBZONE_C')
    final_gdf_spatial.to_file(OUTPUT_GEOJSON, driver='GeoJSON')
    
    final_df.to_csv(OUTPUT_CSV, index=False)
    
    print(f"✅ Step 2 Global complete. Results saved to {OUTPUT_CSV}.")

if __name__ == "__main__":
    main()
