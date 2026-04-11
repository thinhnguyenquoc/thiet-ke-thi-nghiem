# Urban Mobility Model Report: Seoul City-Wide Analysis

## Executive Summary
This report summarizes the comparative validation of three cumulative human mobility models for **Seoul**, South Korea. Using a dataset of **406 origin subzones** and **101,185 Points of Interest (POIs)**, we quantified the predictive improvement of incorporating both **spatial structure (Shells)** and **urban attraction (POIs)** into a multi-model framework.

---

## 1. Study Profile
- **Geography**: Seoul Metropolitan Area (421 Administrative Subzones).
- **Coordinate System**: **EPSG:5179 (UTM-K)**, optimized for high-precision Euclidean distances.
- **POI Dataset**: 101,185 total features including `amenity`, `leisure`, `office`, `public_transport`, `shop`, and `tourism`.

---

## 2. Methodology: Triple-Model Comparison
We evaluated the accuracy $(\text{CPC})$ across three distinct layers of model complexity:

| Model | Classification | Core Logic | Description |
| :--- | :--- | :--- | :--- |
| **Global Probabilistic** | Baseline | Global distance-decay $P(bin_k)$ | Unconstrained decay model. |
| **Uniform Null** | Null Model | Shell Constraint + Equal allocation | Within-bin homogeneous distribution. |
| **Attraction-Weighted**| Full Model | Shell Constraint + POI count ($A_j$) | Within-bin heterogeneous distribution. |

> [!IMPORTANT]
> The **Global Probabilistic** model conserves total trip production (Out-flow) but is not constrained by destination attraction (In-flow).

> [!NOTE]
> The POI attraction weight ($A_j$) is defined as the **simple total count** of all Point-of-Interest occurrences within a subzone.

---

## 3. Comparative Results (Step 6 Summary)

The study reveals a strong hierarchical improvement in spatial overlap (CPC) as each layer of spatial logic is added.

| Model Version | Average **CPC** | Average **$R^2$** | Model Contribution |
| :--- | :--- | :--- | :--- |
| Global Probabilistic | 0.5880 | 0.6120 | Baseline distance decay |
| Uniform Null | 0.7205 | 0.7375 | **+22.5% gain** from shell constraint |
| **Attraction-Weighted**| **0.7623** | **0.7842** | **+5.8% gain** from urban logic |

### Key Insights:
- **Structural Mastery in Seoul**: Moving from the global model to the **Uniform Null Model** proporciona the largest gain (**+22.5%**). This confirms that Seoul's mobility is fundamentally dictated by strict distance-dependent histograms.
- **Predictive Peak**: The **Attraction-Weighted Model** achieves a high **0.762 CPC** city-wide, proving that localized POI features successfully resolve destination choice within the 1km distance shells.
- **Robust Complexity**: The model remains consistent across all 406 districts, successfully validating the 2-step gravity logic for high-density Asian urbanism.

---

## 4. Documentation Index
- **Full Comparative Metrics**: [step6_evaluation_comparison.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step6_evaluation_comparison.csv)
- **POI Attraction Data**: [pois_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/pois_by_zone.csv)
- **Model Result Files**: [step3 (Uniform)](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step3_gravity_results.csv), [step4 (Weighted)](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step4_gravity_results.csv), [step5 (Global)](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step5_gravity_results.csv)
- **Extraction Source**: [detail_pois.geojson](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/detail_pois.geojson)
