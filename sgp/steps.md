## step 1: [DONE]
- [x] Mỗi zone lập histogram chia bin giả sử 1 bin 1km.
- [x] Dữ liệu lấy từ `data_trip_sum.csv`
- [x] Lưu thông tin vào file csv ([binned_trips_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/binned_trips_by_zone.csv))

## step 2: [DONE]
- [x] Lấy thông tin POI trong file 
- [x] Dữ liệu lấy từ `detail_pois.geojson` trích xuất ra file ([pois_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/pois_by_zone.csv))
- [x] Tính khoảng cách từ zone ${i}$ đến các zone còn lại, lấy center tới center theo công thức Euclid
- [x] Các zone $j$ thuộc $bin_k$ (tức là $bin_k$ chứa center của zone $j$)
- [x] Lấy count(POI) của các zone còn lại là lực hấp thụ ($A_j$)
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
  $$ \hat{T}_{ij} = O_{i} \times P(\text{bin}_{k}) \times \frac{A_j}{\sum_{z \in \text{bin}_{k}} A_z} $$
  Trong đó:
  - $\hat{T}_{ij}$: lượng người di chuyển dự đoán từ zone $i$ đến zone $j$
  - $O_i$: Tổng số lượng di chuyển từ zone $i$
  - $A_j$: Số POI của zone $j$
  - $P(\text{bin}_{k})$: xác suất di chuyển vào khoảng cách bin chứa zone $j$ (từ histogram)
- [x] Ráp công thức hấp thụ và khuếch tán tính lượng người di chuyển từ zone ${i}$ đến các zone khác
- [x] Lưu lại kết quả ([step4_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step4_gravity_results.csv))

## step 5: [DONE]
- [x] Kiểm tra kết quả dự đoán với dữ liệu thực tế bằng CPC, R^2, MAE, RMSE cho 2 version (Uniform vs Weighted)
- So sánh kết quả xem có cải thiện version POI so với version no POI không
- [x] Lưu kết quả ([step5_evaluation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step5_evaluation_results.csv))

## step 6: [DONE]
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

- [x] Lưu kết quả ([step6_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step6_radiation_results.csv))

## step 7: [DONE]
- [x] Hiện thực mô hình gravity distance decay function (Parametric)
### Công thức tổng quát:
$$ T_{ij} = \frac{m_i^\alpha n_j^\beta}{f(r_{ij})} $$

Trong đó:
- **$T_{ij}$**: Số lượng cá nhân di chuyển từ địa điểm gốc $i$ đến địa điểm đích $j$.
- **$m_i$**: Quy mô dân số tại địa điểm gốc $i$.
- **$n_j$**: Quy mô dân số tại địa điểm đích $j$.
- **$\alpha$** và **$\beta$**: Các tham số điều chỉnh quy mô dân số.
- **$f(r_{ij})$**: Hàm cản trở khoảng cách (Power / Exponential).

- [x] luu ket qua tham so uoc luong vao file [step7_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step7_gravity_results.csv)

## step 8: [DONE]
- [x] điều chỉnh mô hình radiation ở step 6 theo hướng $s_{ij}$ là tổng POI
- [x] luu ket qua vao file [step8_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/sgp/step8_radiation_results.csv)

## step 9: [DONE]
- [x] so sánh kết quả 6 mô hình bằng CPC, R^2, MAE, RMSE
- [x] cap nhat vao REPORT.md