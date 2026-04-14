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

## 3. Comparative Results (Singapore City-Wide Average)

The study reveals a strong hierarchical improvement in spatial overlap (CPC) as we move from functional models to discrete structural models. In Singapore, while POI improves the Power Law form, the Exponential form remains stable across both mass types.

| Model Version | Mass/Attraction | **CPC** | **$R^2$** | **MAE** (Trips) |
| :--- | :--- | :--- | :--- | :--- |
| **Radiation** | Population | 0.4042 | -1.78 | 473.55 |
| **Radiation** | **POI ($A_j$)** | 0.4087 | -1.16 | 458.12 |
| **Power Decay** | Population | 0.4846 | 0.29 | 365.12 |
| **Power Decay** | **POI ($A_j$)** | **0.5146** | **0.51** | **312.45** |
| **Exponential Decay** | Population | 0.5360 | 0.60 | 298.34 |
| **Exponential Decay** | **POI ($A_j$)** | **0.5354** | **0.53** | **315.12** |
| **Attraction-Uniform** | Shell Layout | 0.7011 | 0.76 | 211.45 |
| **Attraction-Weighted**| **Shells + POIs** | **0.7554** | **0.81** | **185.34** |

### Key Insights:
- **Parametric Stability**: Khác với Seoul, tại Singapore, mô hình **Exponential Gravity** cho kết quả rất ổn định (CPC ~0.53) dù dùng Dân số hay POI. Điều này có thể do quy hoạch đô thị của Singapore tích hợp rất tốt dân cư và tiện ích.
- **Improved Power Law**: Việc sử dụng POI giúp mô hình Power Law cải thiện CPC từ **0.48** lên **0.51**, cho thấy POI vẫn là một chỉ số quan trọng cho sức hấp dẫn điểm đến.
- **Law of Scale-Dependency**: Mô hình **Attraction-Weighted** (giải thuật đề xuất) vẫn vượt trội hoàn toàn với CPC **0.75**, khẳng định quy luật di chuyển dựa trên khoanh vùng khoảng cách (shells) có tính phổ quát cao trên các thành phố khác nhau.

---

## 4. Documentation Index
- **Full Comparative Metrics**: [step9_full_comparison.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step9_full_comparison.csv)
- **Radiation POI Results**: [step8_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step8_radiation_results.csv)
- **Gravity Decay Parameters**: [step7_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step7_gravity_results.csv)
- **Radiation Pop Results**: [step6_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step6_radiation_results.csv)
- **Model Result Files**: [step3 (Uniform)](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step3_gravity_results.csv), [step4 (Weighted)](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step4_gravity_results.csv)
