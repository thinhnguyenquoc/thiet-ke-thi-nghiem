# Cross-City Mobility Research Report: Singapore vs. Seoul Validation

## 1. Executive Summary
This report presents a comparative scientific validation of the **Bin-Constrained Gravity Model** across two major Asian metropolises: **Singapore** and **Seoul**. By evaluating over **130,000 Origin-Destination (OD) pairs** and **200,000 Points of Interest (POIs)**, we demonstrate that human mobility in high-density urban environments follows a universal scale-dependent law. Integrating spatial shell constraints and urban context consistently provides superior predictive accuracy compared to traditional global models.

---

## 2. Multi-Model Performance Comparison (Specific Metrics)

The core of our research involved comparing three levels of model complexity to identify the marginal utility of spatial structure and urban attraction.

### 2.1 Side-by-Side Accuracy Metrics (CPC)

| Model Version | Classification | **Singapore (CPC)** | **Seoul (CPC)** | Model Logic |
| :--- | :--- | :--- | :--- | :--- |
| **Global Probabilistic** | Baseline | 0.5050 | 0.5880 | Basic distance-decay decay. |

> [!IMPORTANT]
> The **Global Probabilistic** model is a singly-constrained baseline that only conserves the total production (Out-flow) of each origin. It does not account for destination attraction constraints, meaning that predicted total **In-flow** at any given subzone may significantly deviate from observed values.
| **Uniform Null** | Structural | 0.6027 | 0.7205 | Radial Shell (1km) constraints. |
| **Attraction-Weighted**| Full Model | **0.6764** | **0.7623** | Shell + POI total count ($A_j$). |

> [!NOTE]
> In this study, the POI attraction weight ($A_j$) is defined as the **simple total count** of all Point-of-Interest occurrences within a subzone. We use the raw sum of POIs across all categories without additional weighting coefficients to ensure a consistent and objective comparison across different city infrastructures.

---

## 3. Detailed Gain Analysis: What Drives Accuracy?

We analyzed the "Incremental Gain" (Improvement) as we added each layer of the mobility law.

### 3.1 The "Shell Jump" (Structural Gain)
Transitioning from a Global Baseline to a **Uniform Null Model** (introducing 1km ring constraints):
- **Singapore**: **+19.3%** increase in spatial overlap.
- **Seoul**: **+22.5%** increase in spatial overlap.
- **Verdict**: In both cities, the **radial distance structure** is the single most powerful predictor of mobility, providing a ~20% accuracy boost.

### 3.2 The "POI Uplift" (Contextual Gain)
Transitioning from a Uniform Null Model to the **Attraction-Weighted Model** (introducing POIs):
- **Singapore**: **+12.2%** final boost.
- **Seoul**: **+5.8%** final boost.
- **Verdict**: POI data provides a significant "Contextual Refinement." While the gain in Seoul is smaller in percentage terms, it is statistically robust, helping the model breach the **0.75 CPC** threshold.

---

## 4. Multi-City Contrast: Comparative R^2 Performance

While CPC measures spatial overlap, $R^2$ indicates how well the model predicts the **variance** of flows across the entire urban grid.

| City | Uniform Null ($R^2$) | **Attraction-Weighted ($R^2$)** | Correlation Improvement |
| :--- | :--- | :--- | :--- |
| **Singapore** | 0.5347 | **0.6256** | **+17.0%** |
| **Seoul** | 0.7375 | **0.7842** | **+6.3%** |

### Observation: 
Singapore's mobility variance is significantly more difficult to predict without urban context (POIs). In Seoul, the distance bins already capture nearly 74% of the variance, confirming a more monocentric or distance-dictated urban form.

---

## 5. Conclusion: A Unified Urban Mobility Law
Our cross-city validation confirms three universal truths about Asian megacity mobility:
1.  **Distance is Primary**: Respecting the 1km distance-shell constraint is mandatory for any high-precision modeling.
2.  **POIs are the Differentiator**: Urban logic (POIs) is the primary driver for choosing specific destinations within a reachable distance range.
3.  **Consistency**: The 2-step logic remains stable (CPC > 0.67) regardless of the city's specific topology, making it a reliable tool for planners across the continent.

---

## 6. Project Data Repository
- **Singapore Deep-Dive**: [sgp/REPORT.md](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/REPORT.md)
- **Seoul Deep-Dive**: [su/REPORT.md](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/REPORT.md)
- **Global comparative Metrics**: [sgp/step6_evaluation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step6_evaluation_results.csv), [su/step6_evaluation_comparison.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step6_evaluation_comparison.csv)
