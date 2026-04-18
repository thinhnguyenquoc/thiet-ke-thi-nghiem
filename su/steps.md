# Modern Mobility Modeling Pipeline: Seoul Case Study (SU)

Tài liệu này hướng dẫn các bước thực hiện để kiểm chứng **Quy luật di chuyển phụ thuộc quy mô (Scale-Dependent Mobility Law)** tại Seoul.

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
- **Công thức**: Xem mục 1.1 (Attraction-Uniform).
- **Mô tả**: Phân bổ đều sản lượng $O_i^{out}$ dựa trên $P(\text{bin}_{k})$. Luồng nội vùng được giữ làm ground truth.

### Step 4: Mô hình Attraction-Weighted (Sử dụng POI) [DONE]
- **Script**: `step4_model_poi.py`
- **Công thức**: Xem mục 1.1 (Attraction-Weighted).
- **Mô tả**: Sử dụng trọng số POI ($B_j+\epsilon$) để phân bổ dòng chảy trong mỗi bin. Luồng nội vùng được giữ làm ground truth.

---

## Phase 3: Mô hình đối chứng (Baselines)

### Step 5: Mô hình Radiation (Dân số & POI) [DONE]
- **Scripts**: `step6_radiation.py` (Population) và `step8_radiation_poi.py` (POI)
- **Công thức**: Xem mục 2. Luồng nội vùng được giữ làm ground truth.

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
- **Mô tả**: Gom các vùng thành $N = [Z/2, Z/3, \dots, Z/10]$ nhóm địa lý.
- **Cơ chế chọn mẫu**:
  - Phân cụm không gian (Spatial Clustering) sử dụng **K-Means** dựa trên tọa độ $(X, Y)$ của các vùng để chia thành $N$ nhóm.
  - **Lặp 20 lần**: Trong mỗi lần lặp, chọn **ngẫu nhiên 1 vùng đại diện** duy nhất trong mỗi cụm để lấy phân phối xác suất ($P_{bin}$) huấn luyện.
  - Các vùng còn lại trong cụm sẽ "mượn" (map) phân phối xác suất của vùng đại diện đó để thực hiện dự báo.
- **Kết quả**: Biểu đồ ổn định CPC [step10_cpc_growth_curve.png](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step10_cpc_growth_curve.png)
