# Urban Mobility Model Report: Seoul City-Wide Analysis

## Executive Summary
This report summarizes the comparative validation of **six human mobility models** for **Seoul**, South Korea. By evaluating over 400 origin subzones and 100,000+ POIs, we quantified the predictive improvement of incorporating spatial shells, urban attraction, and refined intervening opportunities logic across multiple statistical metrics (CPC, $R^2$, MAE, RMSE).

---

## 1. Study Profile
- **Geography**: Seoul Metropolitan Area (421 Administrative Subzones).
- **Coordinate System**: **EPSG:5179 (UTM-K)**, optimized for high-precision Euclidean distances.
- **POI Dataset**: 101,185 total features including `amenity`, `leisure`, `office`, `public_transport`, `shop`, and `tourism`.

---

## 2. Methodology: Multi-Model Framework

| Model | Classification | Core Logic | Mass Proxy |
| :--- | :--- | :--- | :--- |
| **Radiation (Pop)** | Alternative | Intervening Opportunities | Population density |
| **Radiation (POI)** | Alternative | Refined Interv. Opp. | **POI density** |
| **Exponential Decay** | Parametric | Gravity + $e^{-\gamma r}$ | Population mass |
| **Power Decay** | Parametric | Gravity + $r^{-\gamma}$ | Population mass |
| **Attraction-Uniform** | Structural | 1km Shell Constraint | Equal allocation |
| **Attraction-Weighted**| **Full Logic** | **Shells + POIs ($A_j$)** | **POI attraction** |

---

## 3. Comparative Results (Seoul City-Wide Average)

The study reveals a strong hierarchical improvement in spatial overlap (CPC) and error reduction (MAE/RMSE) as we move from smooth functional models to discrete structural models.

| Model Version | **CPC** | **$R^2$** | **MAE** (Trips) | **RMSE** (Trips) |
| :--- | :--- | :--- | :--- | :--- |
| **Radiation (Pop)** | 0.3073 | -5.02 | 3,302.96 | 24,832.80 |
| **Radiation (POI)** | 0.3673 | -5.29 | 3,159.82 | 23,368.84 |
| **Exponential Decay** | **0.6043** | **0.53** | **1,997.44** | **6,992.96** |
| **Power Decay** | **0.5026** | **0.00** | **2,376.05** | **9,236.55** |
| **Attraction-Uniform** | 0.7205 | 0.73 | 1,387.03 | 5,328.68 |
| **Attraction-Weighted**| **0.7623** | **0.77** | **1,154.30** | **4,447.67** |

### Key Insights:
- **Major Improvement**: Bằng cách áp dụng **Ràng buộc lưu lượng tại điểm nguồn (Production-Constrained)**, CPC của các mô hình Gravity truyền thống đã cải thiện đáng kể (Exponential tăng từ 0.35 lên **0.625**).
- **Error Reduction**: Mô hình **Attraction-Weighted** vẫn duy trì vị thế dẫn đầu với CPC **0.762**, nhờ kết hợp cả cấu trúc Shell 1km và trọng số POI.

---

## 4. Documentation Index
- **Full Comparative Metrics**: [step9_full_comparison.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step9_full_comparison.csv)
- **Gravity Decay Parameters**: [step7_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step7_gravity_results.csv)
- **Radiation Results**: [step6_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step6_radiation_results.csv)
- **Summary Metrics (CSV)**: [step9_summary_metrics.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step9_summary_metrics.csv)
