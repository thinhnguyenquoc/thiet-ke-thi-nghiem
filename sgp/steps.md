# Quy trình Mô hình hóa Di động Singapore (Standardized Pipeline)

Tài liệu này hướng dẫn các bước thực hiện để kiểm chứng **Quy luật di chuyển phụ thuộc quy mô (Scale-Dependent Mobility Law)**.

## Các mô hình toán học (Mathematical Models)

> [!NOTE]
> Tất cả các mô hình dưới đây chỉ áp dụng cho luồng di chuyển giữa các vùng khác nhau (**$j \neq i$**). Các luồng nội vùng ($i \to i$) được xử lý như dữ liệu thực tế đã biết (**ground truth**) và luôn mặc định là chính xác trong quá trình đánh giá.

### 1. Mô hình Shell (Production-Constrained)
Đây là mô hình cốt lõi của nghiên cứu, kết hợp xác suất khoảng cách thực nghiệm $P(r)$ và trọng số hấp dẫn $B_j$:
$$\hat{T}_{ij} = O_i \times P(\text{bin}_{k}|i) \times P(j|bin_k, i), \quad \text{với } j \neq i$$
Trong đó:
- **Attraction-Uniform**: $P(j|bin_k, i) = \frac{1}{\sum_{z \in \text{bin}_{k}, z \neq i} 1}$
- **Attraction-Weighted**: $P(j|bin_k, i) = \frac{B_j+\epsilon}{\sum_{z \in \text{bin}_{k}, z \neq i} (B_z+\epsilon)}$
- $O_i$: Tổng sản lượng thực tế tại vùng $i$ (chỉ tính các chuyến đi đi ra ngoài).
- $P(\text{bin}_{k}|i)$: Xác suất di chuyển rơi vào dải khoảng cách ứng với bin $k$.
- $B_j$: Khối lượng hấp dẫn (POI) tại vùng $j$.
- $\epsilon = 1$: Hằng số làm mịn cho các vùng có 0 POI.

### 2. Mô hình Radiation
$$\hat{T}_{ij} = O_i \frac{m_i n_j}{(m_i + s_{ij})(m_i + n_j + s_{ij})}, \quad \text{với } j \neq i$$
- $m_i$: Dân số (hoặc POI) tại vùng nguồn $i$.
- $n_j$: Dân số (hoặc POI) tại vùng đích $j$.
- $s_{ij}$: Tổng dân số (hoặc POI) trong vòng tròn tâm $i$, bán kính $r_{ij}$ (không tính $i$ và $j$).

### 3. Mô hình Gravity (Parametric Decay)
$$\hat{T}_{ij} = O_i \frac{f(r_{ij}) B_j}{\sum_{k, k \neq i} f(r_{ik}) B_k}, \quad \text{với } j \neq i$$
- **Power Law**: $f(r) = r^{-\gamma}$
- **Exponential Law**: $f(r) = e^{-\beta r}$

---

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
- **Công thức**: Xem mục 1.1 (Attraction-Uniform).
- **Mô tả**: Dự báo luồng di chuyển liên vùng ($j \neq i$) bằng cách phân bổ đều sản lượng $O_i^{out}$ dựa trên $P(\text{bin}_{k})$. Luồng nội vùng được giữ làm ground truth.

### Step 4: Mô hình Attraction-Weighted (Sử dụng POI) [DONE]
- **Script**: `step4_model_poi.py`
- **Công thức**: Xem mục 1.1 (Attraction-Weighted).
- **Lưu ý**: Sử dụng hằng số làm mịn $\epsilon = 1$ cho các vùng không có POI. Luồng nội vùng được giữ làm ground truth.

---

## Phase 3: Mô hình đối chứng (Baselines)

### Step 5: Mô hình Radiation (Dân số & POI) [DONE]
- **Scripts**: `step6_radiation.py` (Population) và `step8_radiation_poi.py` (POI)
- **Công thức**: Xem mục 2. Luồng nội vùng được giữ làm ground truth.

### Step 6: Mô hình Gravity Distance-Decay (Tham số) [DONE]
- **Script**: `step7_gravity_decay.py`
- **Mô tả**: Hiện thực hàm Power-law và Exponential decay cho cả Dân số và POI.

---

## Phase 4: Đánh giá & Kiểm chứng

### Step 7: So sánh hiệu suất tổng thể [DONE]
- **Script**: `step9_full_comparison.py`
- **Đầu ra**: Báo cáo tổng hợp hiệu suất (CPC, R², MAE, RMSE) tại [REPORT.md](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/REPORT.md).

### Step 8: Thử nghiệm hiệu quả dữ liệu (Partial-Training Shell)
- **Vai trò**: Chuyên gia phân tích dữ liệu không gian.
- **Mục tiêu**: Đo lường mức độ suy giảm của mô hình shell cải tiến khi giảm lượng dữ liệu huấn luyện.
- **Yêu cầu thực hiện**:
    1. **Hàm bootstrap_analysis**:
       - Input: `OD_matrix` (DataFrame), `ratios = [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.5, 0.8]`.
       - Mỗi tỷ lệ chạy 20 lần, lấy mẫu ngẫu nhiên theo số lượng bản ghi (rows).
    2. **Tính toán CPC (Common Part of Commuters)**:
       Công thức: $CPC = \frac{2 \sum \min(T_{obs}, T_{pred})}{\sum T_{obs} + \sum T_{pred}}$
    3. **Trực quan hóa**:
       - Biểu đồ đường thể hiện CPC trung bình qua các tỷ lệ.
       - Dải sai số (shaded area) thể hiện độ lệch chuẩn (std).
    4. **Phân tích**: Xác định điểm đạt 95% giá trị CPC tối đa (tại 100% data).

- **Script**: `step10_bootstrap_cpc.py` [DONE]
- **Kết quả**:
    - **Maximum CPC**: 0.7292
    - **Điểm bão hòa tối ưu**: Ngưỡng **5.0% dữ liệu** vẫn là lựa chọn tối ưu cho Singapore. Tại đây, CPC đạt ~0.73 và **độ lệch chuẩn giảm xuống còn 0.016**, giúp đảm bảo sự ổn định của mô hình so với mức biến động cao tại ngưỡng 1% (Std = 0.035).
    - **Biểu đồ**: [step10_bootstrap_cpc_decay.png](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step10_bootstrap_cpc_decay.png)

