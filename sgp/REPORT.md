# Comparative Mobility Analysis: A 3-Model Investigation

## Executive Summary
This report summarizes a city-wide evaluation of three distinct human mobility models for Singapore (N=303 subzones). By comparing a **Global Probabilistic Baseline**, a **Uniform Null Model**, and an **Attraction-Weighted Gravity Model**, we quantify the impact of both **spatial structure** and **urban attraction** on predictive accuracy.

---

## 1. Model Definitions

| Model | Classification | Core Logic | Normalization |
| :--- | :--- | :--- | :--- |
| **Global Probabilistic** | Baseline | Global distance-decay probability $P(bin_k)$ | City-wide sum |
| **Uniform Null** | Null Model | 1km Shell/Ring Constraint + Equal allocation | Within-bin shells |
| **Attraction-Weighted**| Full Model | 1km Shell/Ring Constraint + POI count ($A_j$) | Within-bin shells |

> [!IMPORTANT]
> The **Global Probabilistic** model is a singly-constrained baseline. While it successfully conserves the total trip production (Out-flow) of each origin, it does not guarantee that predicted total **In-flow** at destinations will match observed data.

> [!NOTE]
> The POI attraction weight ($A_j$) is defined as the **simple total count** of all Point-of-Interest occurrences within a subzone.

---

## 2. Global Results (Mean performance across 303 subzones)

The results demonstrate a clear hierarchical improvement in accuracy as spatial and contextual constraints are added.

| Model Version | Average **CPC** | Average **$R^2$** | Model Contribution |
| :--- | :--- | :--- | :--- |
| Global Probabilistic | 0.5050 | 0.2550 | Baseline mobility law |
| Uniform Null | 0.6027 | 0.5347 | **+19.3% gain** from shell constraint |
| **Attraction-Weighted**| **0.6764** | **0.6256** | **+12.2% gain** from urban context |

---

## 3. Analysis and Conclusion
- **The Value of Shell Logic**: The transition from the Global model to the **Uniform Null Model** shows that simply forcing the model to respect 1km distance shells (spatial constraints) improves prediction by nearly **20%**. 
- **The Value of Urban Attraction**: The final transition to the **Attraction-Weighted Model** demonstrates that Point-of-Interest data is the critical layer that allows the model to differentiate between destinations within the same distance range, leading to our peak performance of **0.676 CPC**.
- **Validated Hypothesis**: The scale-dependent transition hypothesis is supported by the fact that local attraction features (POIs) only reach their full potential when combined with a robust distance-shell structure.

---

## 4. Documentation Index
- **Comparative Metrics**: [step6_evaluation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/step6_evaluation_results.csv)
- **Predictions (All Versions)**: [step3](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/step3_gravity_results.csv), [step4](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/step4_gravity_results.csv), [step5](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/step5_gravity_results.csv)
- **Workflow Script**: [run_full_comparison.py](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/run_full_comparison.py)
