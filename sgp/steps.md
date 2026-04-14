## step 1: [DONE]
- [x] Mỗi zone lập histogram chia bin giả sử 1 bin 1km.
- [x] Dữ liệu lấy từ `data_trip_sum.csv`
- [x] Lưu thông tin vào file csv ([binned_trips_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/binned_trips_by_zone.csv))

## step 2: [DONE]
- [x] Lấy thông tin POI trong file 
- [x] Dữ liệu lấy từ `detail_pois.geojson` trích xuất ra file ([pois_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/pois_by_zone.csv))
- [x] Tính khoảng cách từ zone ${i}$ đến các zone còn lại, lấy center tới center theo công thức Euclid
- [x] Các zone $j$ thuộc $bin_k$ (tức là $bin_k$ chứa center của zone $j$)
- [x] Lấy count(POI) của các zone còn lại là lực hấp thụ ($B_j + \epsilon$)
- [x] Công thức tính phân bổ xuất phát từ zone ${i}$ đến các zone khác (Logic 2 bước)

## step 3: [DONE] Version Attraction-Uniform (No POI)
  $$ \hat{T}_{ij} = O_{i} \times \frac{P(\text{bin}_{k})}{N_k} $$
  Trong đó:
  - $\hat{T}_{ij}$: lượng người di chuyển dự đoán từ zone $i$ đến zone $j$
  - $O_i$: Tổng số lượng di chuyển từ zone $i$
  - $P(\text{bin}_{k})$: xác suất di chuyển vào khoảng cách bin chứa zone $j$ (từ histogram)
  - $N_k$: Số lượng zone đích nằm trong khoảng cách $bin_k$ (chia đều lượng người)
- [x] Ráp công thức tính lượng người di chuyển từ zone ${i}$ đến các zone khác
- [x] Lưu lại kết quả ([step3_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step3_gravity_results.csv))

## step 4: [DONE] Version Attraction-Weighted (POI)
  $$ \hat{T}_{ij} = O_{i} \times P(\text{bin}_{k}) \times \frac{B_j+\epsilon}{\sum_{z \in \text{bin}_{k}} (B_z+\epsilon)} $$
  Trong đó:
  - $\epsilon = 1$
  - $\hat{T}_{ij}$: lượng người di chuyển dự đoán từ zone $i$ đến zone $j$
  - $O_i$: Tổng số lượng di chuyển từ zone $i$
  - $B_j$: Số POI của zone $j$
  - $P(\text{bin}_{k})$: xác suất di chuyển vào khoảng cách bin chứa zone $j$ (từ histogram)
- [x] Ráp công thức hấp thụ và khuếch tán tính lượng người di chuyển từ zone ${i}$ đến các zone khác
- [x] Lưu lại kết quả ([step4_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step4_gravity_results.csv))

## step 5: [DONE]
- [x] Hiện thực mô hình radiation (Population-based)
- [x] pop lấy từ file sgp_pop_2025_CN_1km_R2025A_UA_v1.tif
### Công thức tổng quát:
$$ T_{ij} = O_i \frac{m_i \times n_j}{(m_i + s_{ij}) \times (m_i + n_j + s_{ij})} $$

Trong đó:
- **$T_{ij}$**: Số lượng chuyến đi trung bình dự báo từ địa điểm gốc $i$ đến địa điểm đích $j$.
- **$O_i$**: Tổng số lượng di chuyển từ zone $i$ như trong step 3
- **$m_i$**: Quy mô dân số tại gốc $i$.
- **$n_j$**: Quy mô dân số tại đích $j$.
- **$s_{ij}$**: Tổng dân số sinh sống trong vùng tròn tâm $i$ với bán kính $r_{ij}$ (không tính dân số tại $i$ và $j$).

- [x] luu ket qua vao file [step5_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step5_radiation_results.csv)

- [x] điều chỉnh mô hình radiation theo hướng $m_i = POI + \epsilon$, $n_j = POI + \epsilon$, $s_{ij} = POI + \epsilon$
- [x] epsilon = 1
- [x] luu ket qua vao file [step5_radiation_results_poi.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step5_radiation_results_poi.csv)

## step 6: [DONE]
- [x] Hiện thực mô hình gravity distance decay function (Parametric)
### Công thức tổng quát (Production-Constrained):
$$ T_{ij} = A_i \times O_i \times D_j \times f(r_{ij}) $$

Trong đó:
- **$T_{ij}$**: Số lượng cá nhân di chuyển từ địa điểm gốc $i$ đến địa điểm đích $j$ trên một đơn vị thời gian.
- **$O_i$**: Tổng sản lượng (Production) di chuyển thực tế từ gốc $i$.
- **$D_j$**: Sức hấp dẫn (Attractiveness) của điểm đích $j$: $D_j = n_j$ (dân số).
- **$f(r_{ij})$**: Hàm cản trở khoảng cách (Power: $r_{ij}^{-\gamma}$ hoặc Exponential: $e^{-\gamma r_{ij}}$).
- **$A_i$**: Hệ số cân bằng (Balancing Factor):
$$ A_i = \frac{1}{\sum_{j} D_j \times f(r_{ij})} $$
Hệ số này đảm bảo rằng $\sum_j T_{ij} = O_i$.
- lưu kết quả vào file [step6_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step6_gravity_results.csv)
- Một version khác $D_j = B_j + \epsilon$ (POI + 1)
- lưu kết quả vào file [step6_gravity_results_poi.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step6_gravity_results_poi.csv)


## step 7: [DONE]
- [x] so sánh kết quả 6 mô hình bằng CPC, R^2, MAE, RMSE
- [x] cap nhat vao REPORT.md

## step 8: [DONE]
- [x] Thực hiện thử nghiệm **Partial-Training Shell** để kiểm chứng khả năng suy rộng không gian đầu tiên trên Singapore.
- Dùng giải thuật gom cụm gom các vùng thanh 10 nhóm sao cho các vùng trong nhóm liền kề nhau.
- Lấy mẫu ngẫu nhiên (Percentage-based Sampling) với tỷ lệ 1%, 2%, 3%, 4%, 5%, 10%, 20%, 30%, 40%, 50% số lượng vùng trong các nhóm để tính toán $P(\text{bin}_k|i)$ trung bình.
- Nếu tỷ lệ thực tế lớn hơn 1% vì luôn phải chọn ít nhất 1 vùng trong group thì chọn mức tỉ lên cao hơn mức thực tế. Ví dụ mức thực tế là 2.2% thì chọn 3% để bắt đầu.
- Áp dụng phân phối xác suất $\bar{P}(bin_k)$ của từng nhóm áp dụng cho các vùng thuộc nhóm đó để dự báo cho toàn bộ mạng lưới Singapore.

- [x] Vẽ biểu đồ đường cong tăng trưởng độ chính xác tại [step8_cpc_growth_curve.png](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step8_cpc_growth_curve.png).

- [x] Lưu kết quả đánh giá vào file [step8_partial_training_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step8_partial_training_results.csv).

