# Quy trình Mô hình hóa Di động Singapore (Standardized Pipeline)

Tài liệu này hướng dẫn các bước thực hiện để kiểm chứng **Quy luật di chuyển phụ thuộc quy mô (Scale-Dependent Mobility Law)**.

## Phase 1: Chuẩn bị dữ liệu & Trích xuất đặc trưng

### Step 1: Phân tích Histogram & Chia khoảng cách (Binning) [DONE]
- **Script**: `step1_histogram.py`
- **Mô tả**: Chia khoảng cách di chuyển thành các bin 1km từ dữ liệu `data_trip_sum.csv`.
- **Kết quả**: [binned_trips_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/binned_trips_by_zone.csv)

### Step 2: Trích xuất đặc trưng hấp dẫn (POI) [DONE]
- **Script**: `step2_poi_extraction.py`
- **Mô tả**: Trích xuất số lượng POI từ `detail_pois.geojson` và tính toán ma trận khoảng cách giữa các zone.
- **Kết quả**: [pois_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/pois_by_zone.csv)

---

## Phase 2: Các mô hình Shell (Đề xuất)

### Step 3: Mô hình Attraction-Uniform (Không POI) [DONE]
- **Script**: `step3_model_no_poi.py`
- **Công thức**: $$ \hat{T}_{ij} = O_{i} \times \frac{P(\text{bin}_{k})}{N_k} $$
- **Kết quả**: Lưu phân phối xác suất tại [prob_dist_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/prob_dist_by_zone.csv)

### Step 4: Mô hình Attraction-Weighted (Sử dụng POI) [DONE]
- **Script**: `step4_model_poi.py`
- **Công thức**: $$ \hat{T}_{ij} = O_{i} \times P(\text{bin}_{k}) \times \frac{B_j+\epsilon}{\sum_{z \in \text{bin}_{k}} (B_z+\epsilon)} $$
- **Lưu ý**: Sử dụng hằng số làm mịn $\epsilon = 1$ cho các vùng không có POI.

---

## Phase 3: Mô hình đối chứng (Baselines)

### Step 5: Mô hình Radiation (Dân số & POI) [DONE]
- **Scripts**: `step6_radiation.py` (Population) và `step8_radiation_poi.py` (POI)
- **Công thức**: $$ T_{ij} = O_i \frac{m_i \times n_j}{(m_i + s_{ij}) \times (m_i + n_j + s_{ij})} $$

### Step 6: Mô hình Gravity Distance-Decay (Tham số) [DONE]
- **Script**: `step7_gravity_decay.py`
- **Mô tả**: Hiện thực hàm Power-law và Exponential decay cho cả Dân số và POI.

---

## Phase 4: Đánh giá & Kiểm chứng

### Step 7: So sánh hiệu suất tổng thể [DONE]
- **Script**: `step9_full_comparison.py`
- **Đầu ra**: Báo cáo tổng hợp hiệu suất (CPC, R², MAE, RMSE) tại [REPORT.md](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/REPORT.md).

### Step 8: Thử nghiệm hiệu quả dữ liệu (Partial-Training Shell) [DONE]
- **Script**: `step8_partial_training.py`
- **Mô tả**: gom các zone thành n = [tổng zone /2, tổng zone /3, tổng zone /4, tổng zone /5, tổng zone /6, tổng zone /7, tổng zone /8, tổng zone /9, tổng zone /10] nhóm địa lý, lấy ngẫu nhiên 1 zone đại diện cho nhóm, thực hiện 20 lần. Tính toán CPC trung bình của 20 lần. kết quả so sánh CPC với Mô hình Attraction-Weighted.
- **Kết quả**: Biểu đồ đường cong tăng trưởng CPC tại [step8_cpc_growth_curve.png](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step8_cpc_growth_curve.png).
