import pandas as pd
import geopandas as gpd
import numpy as np
import os
from PIL import Image
from shapely.geometry import Point
from sklearn.linear_model import LinearRegression

# Configuration
SZ_SHAPEFILE = 'sub_zone/data_seoul_subzone.shp'
TRIPS_FILE = 'aggregated_trips.csv'
POP_TIF = 'kor_pop_2025_CN_1km_R2025A_UA_v1.tif'
OUTPUT_FILE = 'step7_gravity_results.csv'
CITY_CRS = 'EPSG:5179'

def calculate_cpc(y_true, y_pred):
    intersection = np.sum(np.minimum(y_true, y_pred))
    total = np.sum(y_true) + np.sum(y_pred)
    if total == 0: return 0
    return 2 * intersection / total

def main():
    print("🚀 Step 9: Gravity Distance Decay Model (Power & Exponential)...")

    # 1. Load Geometries & Population (Copying logic from Step 7)
    print("📖 Loading subzone geometries...")
    gdf = gpd.read_file(SZ_SHAPEFILE)
    gdf['SUBZONE_C'] = gdf['SUBZONE_C'].astype(float)
    
    gdf_utm = gdf.to_crs(CITY_CRS)
    gdf_utm['centroid'] = gdf_utm.geometry.centroid
    
    print("📊 Extracting population from TIFF...")
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
    
    joined = gpd.sjoin(pixel_gdf, gdf.to_crs("EPSG:4326")[['SUBZONE_C', 'geometry']], how="inner", predicate="within")
    zone_pop = joined.groupby('SUBZONE_C')['pop'].sum().to_dict()
    gdf_utm['pop_m'] = gdf_utm['SUBZONE_C'].map(zone_pop).fillna(0)
    
    # 2. Prepare Regression Data
    print("📖 Loading empirical trips and joining population...")
    trips_df = pd.read_csv(TRIPS_FILE)
    trips_df['ORIGIN_SUBZONE'] = trips_df['ORIGIN_SUBZONE'].astype(float)
    trips_df['DESTINATION_SUBZONE'] = trips_df['DESTINATION_SUBZONE'].astype(float)
    
    # Add population data
    pop_lookup = gdf_utm.set_index('SUBZONE_C')['pop_m'].to_dict()
    trips_df['m_i'] = trips_df['ORIGIN_SUBZONE'].map(pop_lookup).fillna(0)
    trips_df['n_j'] = trips_df['DESTINATION_SUBZONE'].map(pop_lookup).fillna(0)
    
    # Calculate Euclidean distance for each trip if not present (or use existing if accurate)
    # The file has 'distance', but let's ensure it's in km or meters as needed.
    # In aggregated_trips.csv, distance is in degrees maybe? No, let's re-calculate in meters/km.
    print("📏 Re-calculating distances in km (UTM-K)...")
    centroids = gdf_utm.set_index('SUBZONE_C')['centroid'].to_dict()
    
    # Efficiently calculate distance for each row
    trips_df['r_ij_km'] = trips_df.apply(
        lambda row: centroids[row['ORIGIN_SUBZONE']].distance(centroids[row['DESTINATION_SUBZONE']]) / 1000.0
        if row['ORIGIN_SUBZONE'] in centroids and row['DESTINATION_SUBZONE'] in centroids else 0.0,
        axis=1
    )
    
    # Filter for regression: T > 0, m_i > 0, n_j > 0, r_ij > 0
    reg_df = trips_df[(trips_df['COUNT'] > 0) & (trips_df['m_i'] > 0) & 
                      (trips_df['n_j'] > 0) & (trips_df['r_ij_km'] > 0.01)].copy()
    
    print(f"📈 Regression data points: {len(reg_df)}")
    
    # Prepare logs
    reg_df['ln_T'] = np.log(reg_df['COUNT'])
    reg_df['ln_m'] = np.log(reg_df['m_i'])
    reg_df['ln_n'] = np.log(reg_df['n_j'])
    reg_df['ln_r'] = np.log(reg_df['r_ij_km'])
    
    model_params = []
    
    # 3. Model A: Power Law Decay
    print("⚛️ Fitting Power Law model: ln(T) = ln(K) + a*ln(m) + b*ln(n) - c*ln(r)")
    X_power = reg_df[['ln_m', 'ln_n', 'ln_r']]
    y = reg_df['ln_T']
    
    model_power = LinearRegression().fit(X_power, y)
    k_power = np.exp(model_power.intercept_)
    alpha_p = model_power.coef_[0]
    beta_p = model_power.coef_[1]
    gamma_p = -model_power.coef_[2] # c in the formula T = K * m^a * n^b / r^c
    
    # Evaluation
    reg_df['T_hat_power'] = k_power * (reg_df['m_i']**alpha_p) * (reg_df['n_j']**beta_p) / (reg_df['r_ij_km']**gamma_p)
    cpc_p = calculate_cpc(reg_df['COUNT'], reg_df['T_hat_power'])
    
    model_params.append({
        'ModelType': 'Power',
        'K': k_power,
        'alpha': alpha_p,
        'beta': beta_p,
        'gamma': gamma_p,
        'CPC': cpc_p
    })
    
    # 4. Model B: Exponential Decay
    print("⚛️ Fitting Exponential model: ln(T) = ln(K) + a*ln(m) + b*ln(n) - c*r")
    X_exp = reg_df[['ln_m', 'ln_n', 'r_ij_km']]
    
    model_exp = LinearRegression().fit(X_exp, y)
    k_exp = np.exp(model_exp.intercept_)
    alpha_e = model_exp.coef_[0]
    beta_e = model_exp.coef_[1]
    gamma_e = -model_exp.coef_[2] # c in the formula T = K * m^a * n^b / e^(c*r)
    
    # Evaluation
    reg_df['T_hat_exp'] = k_exp * (reg_df['m_i']**alpha_e) * (reg_df['n_j']**beta_e) * np.exp(-gamma_e * reg_df['r_ij_km'])
    cpc_e = calculate_cpc(reg_df['COUNT'], reg_df['T_hat_exp'])
    
    model_params.append({
        'ModelType': 'Exponential',
        'K': k_exp,
        'alpha': alpha_e,
        'beta': beta_e,
        'gamma': gamma_e,
        'CPC': cpc_e
    })
    
    # 5. Save Results
    results_df = pd.DataFrame(model_params)
    print(f"💾 Saving Step 9 results to {OUTPUT_FILE}...")
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n📊 GRAVITY MODEL PARAMETERS:")
    print(results_df)
    print(f"✅ Step 9 Complete.")

if __name__ == "__main__":
    main()
