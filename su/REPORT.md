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

The study reveals a strong hierarchical improvement in spatial overlap (CPC) and error reduction (MAE/RMSE) as we move from smooth functional models to discrete structural models. Notably, using **POI Attraction** consistently outperforms **Population Mass** across all parametric models.

| Model Version | Mass/Attraction | **CPC** | **$R^2$** | **MAE** (Trips) |
| :--- | :--- | :--- | :--- | :--- |
| **Radiation** | Population | 0.3073 | -5.02 | 3,302.96 |
| **Radiation** | **POI ($A_j$)** | 0.3673 | -5.29 | 3,159.82 |
| **Power Decay** | Population | 0.5311 | 0.46 | 2,376.05 |
| **Power Decay** | **POI ($A_j$)** | **0.5787** | 0.32 | 1,942.15 |
| **Exponential Decay** | Population | 0.6058 | 0.63 | 1,997.44 |
| **Exponential Decay** | **POI ($A_j$)** | **0.6674** | **0.70** | **1,521.82** |
| **Attraction-Uniform** | Shell Layout | 0.7205 | 0.73 | 1,387.03 |
| **Attraction-Weighted**| **Shells + POIs** | **0.7623** | **0.77** | **1,154.30** |

### Key Insights:
- **POI-Driven Gravity**: Thay thế Dân số bằng POI trong mô hình Gravity cổ điển giúp CPC tăng từ **0.60** lên **0.67** (đối với hàm Exp). Điều này khẳng định POI là biến số mô tả sức hút di chuyển tốt hơn dân số tại quy mô đô thị.
- **Parametric Limitation**: Mặc dù Gravity-POI cải thiện đáng kể, mô hình thực nghiệm **Attraction-Weighted** (giải thuật đề xuất) vẫn duy trì khoảng cách dẫn đầu (+10% CPC). Điều này cho thấy cấu trúc di chuyển thực tế (shells) không thể bị thay thế hoàn toàn bởi các hàm giải tích (Analytical functions) đơn giản như Power hay Exponential.
- **Non-Parametric Advantage**: Giải thuật đề xuất không chỉ chính xác hơn mà còn ổn định hơn (R²=0.77) so với các mô hình phụ thuộc vào việc tối ưu hóa thông số $\gamma$.

---

## 4. Documentation Index
- **Full Comparative Metrics**: [step9_full_comparison.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step9_full_comparison.csv)
- **Gravity Decay Parameters**: [step7_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step7_gravity_results.csv)
- **Radiation Results**: [step6_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step6_radiation_results.csv)
- **Summary Metrics (CSV)**: [step9_summary_metrics.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step9_summary_metrics.csv)
