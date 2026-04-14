## step 1: [DONE]
- [x] Mỗi zone lập histogram chia bin giả sử 1 bin 1km.
- [x] Dữ liệu lấy từ `aggregated_trips.csv`
- [x] Lưu thông tin vào file csv ([binned_trips_by_zone.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/binned_trips_by_zone.csv))

## step 2: [DONE]
- [x] Lấy thông tin POI trên open street map chi tiết như file ../sgp/detail_pois.geojson 
- [x] Dữ liệu lưu vào file `pois_by_zone.csv`
- [x] Tính khoảng cách từ zone ${i}$ đến các zone còn lại, lấy center tới center theo công thức Euclid
- [x] Các zone $j$ thuộc $bin_k$ (tức là $bin_k$ chứa center của zone $j$)
- [x] Lấy count(POI) của các zone còn lại là lực hấp thụ ($A_j$)
- [x] Công thức tính phân bổ xuất phát từ zone ${i}$ đến các zone khác (Logic 2 bước)

## step 3: [DONE] Version no POI
  $$ \hat{T}_{ij} = O_{i} \times \frac{P(\text{bin}_{k})}{N_k} $$
  Trong đó:
  - $\hat{T}_{ij}$: lượng người di chuyển dự đoán từ zone $i$ đến zone $j$
  - $O_i$: Tổng số lượng di chuyển từ zone $i$
  - $P(\text{bin}_{k})$: xác suất di chuyển vào khoảng cách bin chứa zone $j$ (từ histogram)
  - $N_k$: Số lượng zone đích nằm trong khoảng cách $bin_k$ (chia đều lượng người)
- [x] Ráp công thức tính lượng người di chuyển từ zone ${i}$ đến các zone khác
- [x] Lưu lại kết quả ([step3_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step3_gravity_results.csv))

## step 4: [DONE] Version POI
  $$ \hat{T}_{ij} = O_{i} \times P(\text{bin}_{k}) \times \frac{A_j}{\sum_{z \in \text{bin}_{k}} A_z} $$
  Trong đó:
  - $\hat{T}_{ij}$: lượng người di chuyển dự đoán từ zone $i$ đến zone $j$
  - $O_i$: Tổng số lượng di chuyển từ zone $i$
  - $A_j$: Số POI của zone $j$
  - $P(\text{bin}_{k})$: xác suất di chuyển vào khoảng cách bin chứa zone $j$ (từ histogram)
- [x] Ráp công thức hấp thụ và khuếch tán tính lượng người di chuyển từ zone ${i}$ đến các zone khác
- [x] Lưu lại kết quả ([step4_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step4_gravity_results.csv))

## step 5: [DONE]
- [x] Kiểm tra kết quả dự đoán với dữ liệu thực tế bằng CPC, R^2, MAE, RMSE cho 2 version (No POI, POI)
- So sánh kết quả xem có cải thiện version POI so với version no POI không
- [x] Lưu kết quả ([step5_evaluation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step5_evaluation_results.csv))

## step 6: [DONE]
- [x] Hiện thực mô hình radiation
- [x] pop lấy từ file kor_pop_2025_CN_1km_R2025A_UA_v1.tif
### Công thức tổng quát:
$$ \hat{T}_{ij} = O_i \times \frac{m_i \times n_j}{(m_i + s_{ij}) \times (m_i + n_j + s_{ij})} $$

Trong đó:
- **$\hat{T}_{ij}$**: Số lượng chuyến đi trung bình dự báo từ địa điểm gốc $i$ đến địa điểm đích $j$.
- **$O_i$**: Tổng số lượng di chuyển từ zone $i$ như trong step 3
- **$m_i$**: Quy mô dân số tại gốc $i$.
- **$n_j$**: Quy mô dân số tại đích $j$.
- **$s_{ij}$**: Tổng dân số sinh sống trong vùng tròn tâm $i$ với bán kính $r_{ij}$ (không tính dân số tại $i$ và $j$). Đây được gọi là các "cơ hội xen giữa".

- [x] Lưu kết quả ([step6_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step6_radiation_results.csv))

## step 7: [DONE]
- [x] Hien thuc mo hinh gravity distance decay function: power function, exponential function
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

- [x] luu ket qua hai loai mo hinh (tham so uoc luong) vao file [step7_gravity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step7_gravity_results.csv)

## step 8: [DONE]
- [x] điều chỉnh mô hình radiation ở step 6 theo hướng $s_{ij}$ là tổng POI trong vùng tròn tâm $i$ với bán kính $r_{ij}$ (không tính POI tại $i$ và $j$)
- [x] luu ket qua vao file [step8_radiation_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step8_radiation_results.csv)

## step 9: [DONE]
- [x] so sánh kết quả 6 mô hình (Uniform Null, Attraction-Weighted, Radiation, Radiation POI, Power Decay, Exponential Decay) bằng CPC, R^2, MAE, RMSE
- [x] cap nhat vao REPORT.md

## step 10: [DONE]
- [x] Thực hiện thử nghiệm **Partial-Training Shell** để kiểm chứng khả năng suy rộng không gian đầu tiên trên Seoul.
- [x] **Kịch bản 1**: Lấy mẫu ngẫu nhiên (Percentage-based Sampling) với tỷ lệ 1%, 2%, 3%, 4%, 5%, 10%, 20%, 30%, 40%, 50% số lượng vùng khởi hành phục vụ cho việc tính toán $P(\text{bin}_k|i)$ trung bình.
- [x] Áp dụng phân phối xác suất trung bình $\bar{P}(bin_k)$ từ tập huấn luyện để dự báo cho toàn bộ mạng lưới Seoul.
- Tìm ra tỉ lệ phần trăm vùng khởi hành tối thiểu  CPC không còn cái thiện trên 0.5% so với full-training
- hãy vẽ biểu đồ đường cong tăng trưởng độ chính xác CPC theo tỉ lệ phần trăm vùng khởi hành
- [x] Lưu kết quả đánh giá vào file [step10_partial_training_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step10_partial_training_results.csv).

## step 11: [DONE]
- [x] Chia 421 subzones của Seoul thành 10 nhóm (clusters) có kích thước tương đương và liền kề địa lý.
- [x] Sử dụng thuật toán K-Means trên tọa độ centroid để đảm bảo tính nén (compactness) của các cụm.
- [x] Vẽ bản đồ phân cụm không gian ([step11_spatial_clusters.png](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step11_spatial_clusters.png))
- [x] Lưu kết quả đánh giá chi tiết vào file [step11_spatial_grouping_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step11_spatial_grouping_results.csv).
- **Kết quả**: CPC trung bình đạt **0.7235**, khẳng định khả năng suy rộng không gian mạnh mẽ của mô hình.
## step 12: [DONE]
- [x] Tính toán xác suất di chuyển $P(bin_k)$ riêng biệt cho từng cụm (Intra-District Law).
- [x] Sử dụng quy luật theo cụm để dự báo luồng di chuyển cho chính các subzone trong cụm đó.
- [x] Đánh giá độ chính xác (CPC) để so sánh hiệu quả giữa quy luật cấp thành phố, cấp cụm và cấp zone.
- [x] Lưu kết quả vào file [step12_district_laws_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step12_district_laws_results.csv).
- **Kết quả**: CPC trung bình đạt **0.7295**. 

## step 13: [DONE]
- [x] Thực hiện thử nghiệm **Phân tích độ nhạy theo mẫu phân tán (Distributed Sensitivity Analysis)**.
- [x] Lấy mẫu R% subzones đồng thời từ mỗi cụm trong 10 cụm không gian (đảm bảo mẫu phân tán toàn thành phố).
- [x] Thử nghiệm với các dải tỷ lệ lấy mẫu từ 90% xuống đến 10%.
- [x] Thực hiện 20 lần lặp cho mỗi tỷ lệ để lấy giá trị trung bình và sai số.
- [x] Sử dụng quy luật trung bình từ các mẫu phân tán để dự báo OD cho **Toàn bộ Seoul**.
- [x] Vẽ biểu đồ đường cong độ nhạy ([step13_sensitivity_curve.png](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step13_sensitivity_curve.png)).
- [x] Lưu kết quả chi tiết vào file [step13_subzone_sensitivity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step13_subzone_sensitivity_results.csv).
- **Kết quả**: CPC chỉ giảm cực nhẹ (từ 0.7259 xuống 0.7248) ngay cả khi chỉ sử dụng 10% dữ liệu phân tán, khẳng định tính bão hòa thông tin nhanh chóng của quy luật di chuyển.

## step 14: [DONE]
- [x] làm như step 13 nhưng tỉ lệ dữ liệu từ 1% đến 9%
- [x] vẽ biểu đồ suy giảm CPC.
- [x] luu ket qua vao file [step14_subzone_sensitivity_results.csv](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step14_subzone_sensitivity_results.csv).

## step 15: [DONE]
- [x] Tổng hợp kết quả từ Step 13 và Step 14.
- [x] Vẽ biểu đồ đường cong độ nhạy toàn diện ([step15_comprehensive_sensitivity.png](file:///Users/nguyenquocthinh/Documents/thiet-ke-thi-nghiem/su/step15_comprehensive_sensitivity.png)) sử dụng thang đo Logarithmic cho trục X.
- [x] Biểu đồ cho thấy sự ổn định của quy luật di chuyển dải (Shell Law) trên toàn bộ dải lấy mãu từ 1% đến 90%.
