## step 1: [DONE]
- [x] Mỗi zone lập histogram chia bin giả sử 1 bin 1km.
- [x] Dữ liệu lấy từ `data_trip_sum.csv`
- [x] Lưu thông tin vào file csv ([binned_trips_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/binned_trips_by_zone.csv))

## step 2: [DONE]
- [x] Lấy thông tin POI trong file 
- [x] Dữ liệu lấy từ `detail_pois.geojson`
- [x] Tính khoảng cách từ zone ${i}$ đến các zone còn lại, lấy center tới center theo công thức Euclid
- [x] Các zone $j$ thuộc $bin_k$ (tức là $bin_k$ chứa center của zone $j$)
- [x] Lấy count(POI) của các zone còn lại là lực hấp thụ ($A_j$)
- [x] Công thức tính phân bổ xuất phát từ zone ${i}$ đến các zone khác (Logic 2 bước)

## step 3: Version no POI
  $$ \hat{T}_{ij} = O_{i} \times \frac{P(\text{bin}_{k})}{N_k} $$
  Trong đó:
  - $\hat{T}_{ij}$: lượng người di chuyển dự đoán từ zone $i$ đến zone $j$
  - $O_i$: Tổng số lượng di chuyển từ zone $i$
  - $P(\text{bin}_{k})$: xác suất di chuyển vào khoảng cách bin chứa zone $j$ (từ histogram)
  - $N_k$: Số lượng zone đích nằm trong khoảng cách $bin_k$ (chia đều lượng người)
- [x] Ráp công thức tính lượng người di chuyển từ zone ${i}$ đến các zone khác
- [x] Lưu lại kết quả ([step3_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/step3_gravity_results.csv))

## step 4: Version POI
  $$ \hat{T}_{ij} = O_{i} \times P(\text{bin}_{k}) \times \frac{A_j}{\sum_{z \in \text{bin}_{k}} A_z} $$
  Trong đó:
  - $\hat{T}_{ij}$: lượng người di chuyển dự đoán từ zone $i$ đến zone $j$
  - $O_i$: Tổng số lượng di chuyển từ zone $i$
  - $A_j$: Số POI của zone $j$
  - $P(\text{bin}_{k})$: xác suất di chuyển vào khoảng cách bin chứa zone $j$ (từ histogram)
- [x] Ráp công thức hấp thụ và khuếch tán tính lượng người di chuyển từ zone ${i}$ đến các zone khác
- [x] Lưu lại kết quả ([step4_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/step4_gravity_results.csv))

## step 5: only use P(bin)
$$ \hat{T}_{ij} = O_{i} \times P(\text{bin}_{k}) $$
  Trong đó:
  - $\hat{T}_{ij}$: lượng người di chuyển dự đoán từ zone $i$ đến zone $j$
  - $O_i$: Tổng số lượng di chuyển từ zone $i$
  - $P(\text{bin}_{k})$: xác suất di chuyển vào khoảng cách bin chứa zone $j$ (từ histogram)
- [x] Ráp công thức tính lượng người di chuyển từ zone ${i}$ đến các zone khác
- [x] Lưu lại kết quả ([step5_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/step5_gravity_results.csv))


## step 6: [DONE]
- [x] Kiểm tra kết quả dự đoán với dữ liệu thực tế bằng CPC, R^2, MAE, RMSE cho 3 version
- So sánh kết quả xem có cải thiện version POI so với version no POI không
- [x] Lưu kết quả ([step6_evaluation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/step6_evaluation_results.csv))