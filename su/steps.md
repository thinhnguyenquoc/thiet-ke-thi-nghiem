# Modern Mobility Modeling Pipeline: Seoul Case Study (SU)

Tài liệu này hướng dẫn các bước thực hiện để kiểm chứng **Quy luật di chuyển phụ thuộc quy mô (Scale-Dependent Mobility Law)** tại Seoul.

## Phase 1: Chuẩn bị dữ liệu & Trích xuất đặc trưng

### Step 1: Phân tích Histogram & Chia khoảng cách (Binning) [DONE]
- **Script**: `step1_histogram.py`
- **Mô tả**: Chia khoảng cách di chuyển thành các bin 1km từ dữ liệu `aggregated_trips.csv`.
- **Kết quả**: [binned_trips_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/binned_trips_by_zone.csv)

### Step 2: Trích xuất đặc trưng hấp dẫn (POI) [DONE]
- **Script**: `step2_osmnx_pois.py`
- **Mô tả**: Trích xuất số lượng POI chi tiết và tính toán ma trận khoảng cách Euclid giữa các centroid của subzone.
- **Kết quả**: [pois_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/pois_by_zone.csv)

---

## Phase 2: Các mô hình Shell (Đề xuất)

### Step 3: Mô hình Attraction-Uniform (Không POI) [DONE]
- **Script**: `step3_model_no_poi.py`
- **Công thức**: $$ \hat{T}_{ij} = O_{i} \times \frac{P(\text{bin}_{k})}{N_k} $$

### Step 4: Mô hình Attraction-Weighted (Sử dụng POI) [DONE]
- **Script**: `step4_model_poi.py`
- **Công thức**: $$ \hat{T}_{ij} = O_{i} \times P(\text{bin}_{k}) \times \frac{A_j+\epsilon}{\sum_{z \in \text{bin}_{k}} (A_z+\epsilon)} $$

---

## Phase 3: Mô hình đối chứng (Baselines)

### Step 5: Mô hình Radiation (Dân số & POI) [DONE]
- **Scripts**: `step6_radiation.py` (Population) và `step8_radiation_poi.py` (POI)
- **Mô tả**: Sử dụng dữ liệu dân số từ `kor_pop_2025_CN_1km_R2025A_UA_v1.tif`.

### Step 6: Mô hình Gravity Distance-Decay (Tham số) [DONE]
- **Script**: `step7_gravity_decay.py`
- **Mô tả**: Hiện thực hàm Power-law và Exponential decay.

---

## Phase 4: Đánh giá & Kiểm chứng tính bão hòa thông tin

### Step 7: So sánh hiệu suất tổng thể [DONE]
- **Script**: `step9_full_comparison.py`
- **Kết quả**: Báo cáo tổng hợp tại [REPORT.md](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/REPORT.md).

### Step 8: Thử nghiệm hiệu quả dữ liệu (Partial-Training Shell) [DONE]
- **Script**: `step10_partial_training.py`
- **Thuật toán**: 
  - Gom các zone thành $N$ nhóm địa lý ($N = Z/2, Z/3, \dots, Z/10$).
  - Lấy ngẫu nhiên **1 zone đại diện** cho mỗi nhóm.
  - Lặp lại 20 lần cho mỗi giá trị $N$ để tính CPC trung bình.
- **Kết quả**: [step10_cpc_growth_curve.png](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step10_cpc_growth_curve.png)
