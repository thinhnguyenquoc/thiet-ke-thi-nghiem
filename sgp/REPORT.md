# Comparative Mobility Analysis: Singapore Case Study

## Executive Summary
This report summarizes a city-wide evaluation of human mobility models for Singapore (N=303 subzones). By comparing parametric gravity models, radiation models (Population vs POI), and our proposed **Shell-Constrained Gravity Models**, we quantify the impact of spatial structure and urban attraction on predictive accuracy across multiple metrics (CPC, $R^2$, MAE, RMSE).

---

## 1. Study Profile
- **Geography**: Singapore (323 Planning Subzones).
- **Coordinate System**: **EPSG:3414 (SVY21)**, optimized for Singapore.
- **POI Dataset**: Extracted from OSM including retail, amenity, and transport features (Total POIs: 59,704).

---

## 2. Methodology: Framework Comparison

| Model | Classification | Core Logic | Mass Proxy |
| :--- | :--- | :--- | :--- |
| **Radiation (Pop)** | Alternative | Interv. Opportunities | Population density |
| **Radiation (POI)** | Alternative | Refined Interv. Opp. | **POI density** |
| **Exponential Decay** | Parametric | Gravity + $e^{-\gamma r}$ | Population mass |
| **Power Decay** | Parametric | Gravity + $r^{-\gamma}$ | Population mass |
| **Attraction-Uniform**| Structural | 1km Shell Constraint | Equal allocation |
| **Attraction-Weighted**| **Proposed** | **Shells + POIs ($A_j$)** | **POI attraction** |

---

## 3. Comparative Results (Singapore City-Wide Average)

The study reveals a strong hierarchical improvement in spatial overlap (CPC) as we move from functional models to discrete structural models. In Singapore, our proposed Scale-Dependent Mobility Law (Attr-Weighted) achieves the highest precision.

| Model Version | Mass/Attraction | **CPC** | **$R^2$** | **MAE** (Trips) | **RMSE** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Radiation** | Population | 0.2015 | -17.18 | 116.51 | 790.91 |
| **Radiation** | **POI ($A_j$)** | 0.2730 | -10.48 | 102.00 | 622.76 |
| **Power Decay** | Population | 0.4449 | 0.07 | 78.31 | 226.67 |
| **Power Decay** | **POI ($A_j$)** | 0.5234 | 0.07 | 67.12 | 220.75 |
| **Exponential Decay** | Population | 0.4948 | 0.04 | 70.49 | 195.80 |
| **Exponential Decay** | **POI ($A_j$)** | 0.5809 | 0.34 | 59.11 | 170.23 |
| **Attraction-Uniform** | Shell Layout | 0.6027 | 0.53 | 57.26 | 146.78 |
| **Attraction-Weighted**| **Shells + POIs** | **0.6767** | **0.63** | **44.93** | **123.90** |

### Key Insights:
- **Superiority of Scale-Dependent Law**: Mô hình **Attraction-Weighted** đạt CPC cao nhất (**0.677**), khẳng định việc sử dụng cấu trúc khoanh vùng (shells) kết hợp với trọng số POI giúp mô phỏng chính xác nhất hành vi di chuyển trong đô thị nén như Singapore.
- **Parametric Comparison**: Mô hình **Exponential POI** (CPC 0.58) vượt trội hơn hẳn so với Radiation (CPC 0.27), cho thấy khoảng cách địa lý đóng vai trò quan trọng hơn "cơ hội xen kẽ" trong cấu trúc di chuyển ngắn của Singapore.
- **POI Significance**: Trong tất cả các loại mô hình, việc tích hợp dữ liệu POI (59,704 điểm) giúp cải thiện đáng kể độ chính xác so với chỉ dùng dữ liệu dân số. Đặc biệt, Gravity POI (0.58) so với Gravity Pop (0.49).

---

## 4. Documentation Index
- **Full Comparative Metrics**: [step9_full_comparison.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step9_full_comparison.csv)
- **Radiation POI Results**: [step8_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step8_radiation_results.csv)
- **Gravity Decay Parameters**: [step7_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step7_gravity_results.csv)
- **Radiation Pop Results**: [step6_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step6_radiation_results.csv)
- **Model Result Files**: [step3 (Uniform)](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step3_gravity_results.csv), [step4 (Weighted)](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step4_gravity_results.csv)
