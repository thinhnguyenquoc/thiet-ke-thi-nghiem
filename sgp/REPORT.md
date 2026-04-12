# Comparative Mobility Analysis: Singapore Case Study

## Executive Summary
This report summarizes a city-wide evaluation of human mobility models for Singapore (N=303 subzones). By comparing parametric gravity models, radiation models (Population vs POI), and our proposed **Shell-Constrained Gravity Models**, we quantify the impact of spatial structure and urban attraction on predictive accuracy across multiple metrics (CPC, $R^2$, MAE, RMSE).

---

## 1. Study Profile
- **Geography**: Singapore (323 Planning Subzones).
- **Coordinate System**: **EPSG:3414 (SVY21)**, optimized for Singapore.
- **POI Dataset**: Extracted from OSM including retail, amenity, and transport features.

---

## 2. Methodology: Framework Comparison

| Model | Classification | Core Logic | Mass Proxy |
| :--- | :--- | :--- | :--- |
| **Radiation (Pop)** | Alternative | Interv. Opportunities | Population density |
| **Radiation (POI)** | Alternative | Refined Interv. Opp. | **POI density** |
| **Exponential Decay** | Parametric | Gravity + $e^{-\gamma r}$ | Population mass |
| **Power Decay** | Parametric | Gravity + $r^{-\gamma}$ | Population mass |
| **Attraction-Uniform**| Structural | 1km Shell Constraint | Equal allocation |
| **Attraction-Weighted**| **Full Logic** | **Shells + POIs ($A_j$)** | **POI attraction** |

---

## 3. Comparative Results (Singapore Average)

The results demonstrate a clear hierarchy where discrete structural models outperform smooth analytical curves in capturing Singapore's dense urban layout.

| Model Version | **CPC** | **$R^2$** | **MAE** (Trips) | **RMSE** (Trips) |
| :--- | :--- | :--- | :--- | :--- |
| **Radiation (Pop)** | 0.1822 | -9.75 | 107.83 | 625.39 |
| **Radiation (POI)** | 0.2681 | -8.95 | 110.10 | 697.22 |
| **Exponential Decay** | 0.2628 | -0.09 | 69.54 | 258.28 |
| **Power Decay** | 0.3052 | -0.22 | 67.28 | 249.59 |
| **Attraction-Uniform**| 0.6027 | 0.53 | 57.26 | 146.78 |
| **Attraction-Weighted**| **0.6764** | **0.63** | **44.96** | **124.02** |

### Key Insights:
- **Spatial Accuracy**: Using empirical **1km distance shells** (Attraction-Uniform, 0.603 CPC) doubles the spatial overlap compared to the best analytical model (Power Law, 0.305 CPC).
- **Urban Refinement**: The addition of POI data (Attraction-Weighted) reduces the MAE from 57 to **45 trips**, a further **21% reduction in error**.
- **Radiation Improvement**: Switching from population to POIs in the Radiation model significantly improved CPC from **0.18** to **0.27**, similar to the trend observed in Seoul.

---

## 4. Documentation Index
- **Full Comparative Metrics**: [step9_full_comparison.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step9_full_comparison.csv)
- **Radiation POI Results**: [step8_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step8_radiation_results.csv)
- **Gravity Decay Parameters**: [step7_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step7_gravity_results.csv)
- **Radiation Pop Results**: [step6_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step6_radiation_results.csv)
- **Model Result Files**: [step3 (Uniform)](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step3_gravity_results.csv), [step4 (Weighted)](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step4_gravity_results.csv)
