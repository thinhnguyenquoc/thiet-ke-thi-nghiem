import pandas as pd
import geopandas as gpd
import numpy as np
import os
from PIL import Image
from shapely.geometry import Point
from sklearn.linear_model import LinearRegression

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_sgp_subzone.shp'
TRIPS_FILE = 'data_trip_sum.csv'
POP_TIF = 'sgp_pop_2025_CN_1km_R2025A_UA_v1.tif'
OUTPUT_FILE = 'step9_gravity_results.csv'
CITY_CRS = 'EPSG:3414'

def calculate_cpc(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    if total == 0: return 0
    return 2 * intersection / total

def main():
    print("🚀 Step 9 (SINGAPORE): Gravity Distance Decay Model Estimation...")

    # 1. Load Geometries & Population
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    with Image.open(POP_TIF) as img:
        pop_data = np.array(img).astype(float)
        tiepoint = img.tag[33922]
        pixel_scale = img.tag[33550]
        lon_orig, lat_orig = tiepoint[3], tiepoint[4]
        dx, dy = pixel_scale[0], pixel_scale[1]
        rows, cols = pop_data.shape
        c_cols, r_rows = np.meshgrid(np.arange(cols), np.arange(rows))
        lons = lon_orig + (c_cols + 0.5) * dx
        lats = lat_orig - (r_rows + 0.5) * dy
        mask = (pop_data > 0) & (~np.isnan(pop_data))
        pixel_gdf = gpd.GeoDataFrame(
            {'pop': pop_data[mask]}, 
            geometry=[Point(x, y) for x, y in zip(lons[mask], lats[mask])],
            crs="EPSG:4326"
        )
    
    joined = gpd.sjoin(pixel_gdf, gdf[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
    pop_lookup = joined.groupby('SUBZONE_C')['pop'].sum().to_dict()
    
    # 2. Prepare Regression Data
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['m_i'] = trips_df['ORIGIN_SUBZONE'].map(pop_lookup).fillna(0)
    trips_df['n_j'] = trips_df['DESTINATION_SUBZONE'].map(pop_lookup).fillna(0)
    
    centroids = gdf_utm.set_index('SUBZONE_C')['centroid'].to_dict()
    trips_df['r_ij_km'] = trips_df.apply(
        lambda row: centroids[row['ORIGIN_SUBZONE']].distance(centroids[row['DESTINATION_SUBZONE']]) / 1000.0
        if row['ORIGIN_SUBZONE'] in centroids and row['DESTINATION_SUBZONE'] in centroids else 0.0,
        axis=1
    )
    
    reg_df = trips_df[(trips_df['COUNT'] > 0) & (trips_df['m_i'] > 0) & 
                      (trips_df['n_j'] > 0) & (trips_df['r_ij_km'] > 0.01)].copy()
    
    reg_df['ln_T'] = np.log(reg_df['COUNT'])
    reg_df['ln_m'] = np.log(reg_df['m_i'])
    reg_df['ln_n'] = np.log(reg_df['n_j'])
    reg_df['ln_r'] = np.log(reg_df['r_ij_km'])
    
    model_params = []
    
    # Power Law
    X_p = reg_df[['ln_m', 'ln_n', 'ln_r']]
    model_p = LinearRegression().fit(X_p, reg_df['ln_T'])
    kp = np.exp(model_p.intercept_)
    ap, bp, gp = model_p.coef_[0], model_p.coef_[1], -model_p.coef_[2]
    reg_df['T_p'] = kp * (reg_df['m_i']**ap) * (reg_df['n_j']**bp) / (reg_df['r_ij_km']**gp)
    model_params.append({'ModelType': 'Power', 'K': kp, 'alpha': ap, 'beta': bp, 'gamma': gp, 'CPC': calculate_cpc(reg_df['COUNT'], reg_df['T_p'])})
    
    # Exponential
    X_e = reg_df[['ln_m', 'ln_n', 'r_ij_km']]
    model_e = LinearRegression().fit(X_e, reg_df['ln_T'])
    ke = np.exp(model_e.intercept_)
    ae, be, ge = model_e.coef_[0], model_e.coef_[1], -model_e.coef_[2]
    reg_df['T_e'] = ke * (reg_df['m_i']**ae) * (reg_df['n_j']**be) * np.exp(-ge * reg_df['r_ij_km'])
    model_params.append({'ModelType': 'Exponential', 'K': ke, 'alpha': ae, 'beta': be, 'gamma': ge, 'CPC': calculate_cpc(reg_df['COUNT'], reg_df['T_e'])})
    
    results_df = pd.DataFrame(model_params)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print("\n📊 GRAVITY MODEL PARAMETERS (SINGAPORE):")
    print(results_df)

if __name__ == "__main__":
    main()
