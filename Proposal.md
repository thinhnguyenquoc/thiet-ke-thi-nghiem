# 1. Title (Tiêu đề)
Sử dụng mô hình dựa trên phân bổ xác suất di chuyển để ước lượng luồng di chuyển tại các thành phố lớn: Singapre, Seoul
# 2. Abstract
Dữ liệu luồng di chuyển giữa các khu vực trong thành phố rất quan trọng cho các lĩnh vực quy hoạch giao thông, phân tích thị trường, dự báo dịch bệnh. Do đó có nhiều nghiên cứu đã cố gắng ước lượng luồng di chuyển từ nhiều nguồn dữ liệu khác nhau như dữ liệu GPS, dữ liệu điện thoại di động, dữ liệu câu hỏi khảo sát. Tuy nhiên, các phương pháp này đều có những hạn chế về giả định và yêu cầu dữ liệu khắt khe. Nghiên cứu đề xuất một phương pháp ước lượng mới dựa trên phân bổ xác suất di chuyển nhằm cải thiện độ chính xác của các mô hình cũ với sự kết hợp của dữ liệu mở từ Open street map. Kết quả đạt được ...
# 3. Introduction
Các mô hình tương tác không gian truyền thống như Gravity và Radiation từ lâu đã được áp dụng rộng rãi để ước lượng luồng di chuyển (mobility flows) và mang lại nhiều kết quả quan trọng trong quản lý đô thị. Tuy nhiên, khả năng dự báo của các mô hình này thường bị hạn chế bởi những giả định lý thuyết chưa bao quát được sự phức tạp của các siêu đô thị hiện đại.
Cụ thể, mô hình Gravity gặp trở ngại lớn do các tham số suy giảm khoảng cách ($\alpha, \beta$) phụ thuộc chặt chẽ vào dữ liệu lịch sử, khiến nó mất đi tính linh hoạt khi áp dụng cho các khu vực thiếu dữ liệu quan sát [5,12]. Ngược lại, mô hình Radiation dù có lợi thế không tham số (parameter-free) nhưng lại dựa trên giả định đơn điệu về việc tối ưu hóa khoảng cách để tìm kiếm cơ hội [12,8]. Giả định này không còn phù hợp trong bối cảnh các siêu đô thị đa trung tâm, nơi sự phân bổ dày đặc của các điểm tiện ích (Points of Interest - POIs) thúc đẩy các hành vi di chuyển vượt ra ngoài quy luật "gần nhất" để thỏa mãn các nhu cầu dịch vụ đa dạng [8].
Để khắc phục, nhiều nghiên cứu gần đây đã chuyển hướng sang các giải pháp dựa trên dữ liệu (Data-driven), đặc biệt là học máy và học sâu nhằm khai thác thông tin từ OpenStreetMap hoặc ảnh vệ tinh để hiểu cấu trúc không gian [5,7]. Mặc dù cải thiện đáng kể độ chính xác, nhưng các phương pháp này vẫn đòi hỏi tài nguyên tính toán lớn, dữ liệu huấn luyện khổng lồ và thường thiếu khả năng giải thích về mặt cơ chế đô thị [5,9].
Nghiên cứu của chúng tôi đề xuất một hướng tiếp cận mới: sử dụng khung xác suất di chuyển có điều kiện (conditional mobility probability) kết hợp với dữ liệu POI để phục hồi ma trận Origin-Destination (OD). Bằng cách áp dụng ràng buộc đầu ra (Production-constrained)[1], phương pháp này không chỉ tận dụng được dữ liệu mở từ OpenStreetMap mà còn khắc phục trực tiếp yếu điểm của mô hình Radiation trong môi trường siêu đô thị nén như Singapore và Seoul. Hướng tiếp cận này hứa hẹn mang lại một giải pháp cân bằng giữa tính chính xác của dữ liệu thực nghiệm và tính tổng quát của các luật di chuyển hệ thống.
## 3.1 Gravity Models
Dưới đây là công thức của Mô hình Trọng trường (Gravity Model)[1]

$$ T_{ij} = \frac{m_i^\alpha n_j^\beta}{f(r_{ij})} $$

Trong đó
- **$T_{ij}$**: Số lượng cá nhân di chuyển từ địa điểm gốc $i$ đến địa điểm đích $j$ trên một đơn vị thời gian.
- **$m_i$**: Quy mô dân số tại địa điểm gốc $i$.
- **$n_j$**: Quy mô dân số tại địa điểm đích $j$.
- **$r_{ij}$**: Khoảng cách vật lý giữa hai địa điểm $i$ và $j$.
- **$\alpha$** và **$\beta$**: Các số mũ (tham số) có thể điều chỉnh được.
- **$f(r_{ij})$**: Hàm cản trở khoảng cách (deterrence function).

Ví dụ về ước lượng luồng di chuyển bằng mô hình Gravity:
Chúng ta xét hai cặp địa điểm có đặc điểm dân số và khoảng cách rất tương đồng nhau:
Cặp 1 (Bang Utah - UT):
Điểm gốc (Washington County): Dân số $m_i =90.000$ người.
Điểm đích (Davis County): Dân số $n_j =240.000$ người.
Khoảng cách $r_{ij} =447$ km.
Cặp 2 (Bang Alabama - AL):
Điểm gốc (Houston County): Dân số $m_i =89.000$ người.
Điểm đích (Madison County): Dân số $n_j =280.000$ người.
Khoảng cách $r_{ij} =410$ km.

Các tham số của mô hình (Parameters)

Theo công thức Gravity $T_{ij} \propto \frac{m_i^\alpha n_j^\beta}{f(r_{ij})}$, nhóm tác giả đã sử dụng dữ liệu thực tế để huấn luyện và tìm ra bộ tham số tốt nhất cho các chuyến đi có khoảng cách $r>119$ km
. Bộ tham số thu được là:
α=0.24 (hệ số cho dân số điểm gốc)
β=0.14 (hệ số cho dân số điểm đích)
Hàm cản trở khoảng cách $f(r_{ij}) =r_{ij}^c$ với $c=0.29$

Áp dụng tính toán (Calculation)
Khi thay các giá trị vào công thức để dự báo luồng di chuyển (đã bao gồm hằng số tỉ lệ chuẩn hóa từ mô hình), ta có phép tính tỉ lệ như sau:
Đối với cặp ở Utah: 
$T_{UT} \propto \frac{m_i^\alpha n_j^\beta}{f(r_{ij})} = \frac{90000^{0.24} \times 240000^{0.14}}{447^{0.29}}$
Đối với cặp ở Alabama: 
$T_{AL} \propto \frac{m_i^\alpha n_j^\beta}{f(r_{ij})} = \frac{89000^{0.24} \times 280000^{0.14}}{410^{0.29}}$

Kết quả dự báo: Bởi vì dân số ở điểm gốc (90.000≈89.000), dân số ở điểm đích (240.000≈280.000) và khoảng cách (447≈410) của hai cặp này gần như tương đương nhau, mô hình Gravity dự báo số lượng người di chuyển cho cả hai cặp đều là 1 người

## 3.2 Radiation model
Dưới đây là công thức của Mô hình Radiation[12]
$$ T_{ij} = T_i \frac{m_i \times n_j}{(m_i + s_{ij}) \times (m_i + n_j + s_{ij})}$$

Trong đó
- $T_{ij}$: Số lượng chuyến đi (hoặc luồng di cư) trung bình dự báo từ địa điểm gốc i đến địa điểm đích j
- $T_i$: Tổng số lượng người khởi hành (tổng outflows/migrants) rời khỏi địa điểm gốc i
- $m_i$: Quy mô dân số tại địa điểm gốc i
- $n_j$: Quy mô dân số tại địa điểm đích j
- $s_{ij}$: Tổng dân số sinh sống trong vùng không gian hình tròn có tâm tại i và bán kính là khoảng cách $r_{ij}$ (vừa chạm đến điểm j). Biến số này loại trừ (không bao gồm) dân số của bản thân điểm gốc i và điểm đích j

Ví dụ:
Cặp 1: Bang Utah (Khu vực thưa dân)
Dân số gốc (m_i) = 90.000
Dân số đích (n_j) = 240.000
Dân số xen giữa (s_ij) = 2×10^6 (2.000.000)
Tổng lượng người đi làm ước tính: T_i = 0.11×90.000 = 9.900 người.
Tính xác suất chọn điểm đến (P_UT):
Tử số: m_i ×n_j = 90.000×240.000 = 21,6×10^9
Mẫu số 1 (m_i +s_ij): 90.000+2.000.000=2.090.000
Mẫu số 2 (m_i +n_j +s_ij): 90.000+240.000+2.000.000=2.330.000
Xác suất P_UT = (2.090.000×2.330.000)/(21,6×10^9) ≈ 4,87×10^12 / (21,6×10^9) ≈ 0,00443
Dự báo luồng di chuyển tại Utah: T_UT = T_i ×P_UT = 9.900×0,00443 ≈ 43,9 người

Cặp 2: Bang Alabama (Khu vực đông dân)
Dân số gốc (m_i) = 89.000
Dân số đích (n_j) = 280.000
Dân số xen giữa (s_ij) = 2×10^7 (20.000.000)
Tổng lượng người đi làm ước tính: T_i = 0.11×89.000 = 9.790 người.
Tính xác suất chọn điểm đến (P_AL):
Tử số: m_i ×n_j = 89.000×280.000 = 24,92×10^9
Mẫu số 1 (m_i +s_ij): 89.000+20.000.000=20.089.000
Mẫu số 2 (m_i +n_j +s_ij): 89.000+280.000+20.000.000=20.369.000
Xác suất P_AL = (20.089.000×20.369.000)/(24,92×10^9) ≈ 409,2×10^12 / (24,92×10^9) ≈ 0,00006
Dự báo luồng di chuyển tại Alabama: T_AL = T_i ×P_AL = 9.790×0,00006 ≈ 0,59 người


# 4. Methodology
## 4.1 Notation and Data Inputs
## 4.2 Model Structure
## 4.3 Probability Distribution of Trip Lengths


4.2. Probability Distribution of Trip Lengths: Cách bạn xử lý các bin khoảng cách.
4.3. The Proposed Estimation Model: Trình bày các công thức toán học $T_{ij}$.
 +n 
j
​
 +s 
ij
​
 ): 90.000+240.000+2.000.000=2.330.000
Xác suất P 
UT
​
 = 
2.090.000×2.330.000
21,6×10 
9
 
​
 ≈ 
4,87×10 
12
 
21,6×10 
9
 
​
 ≈0,00443
Dự báo luồng di chuyển tại Utah: 
T 
UT
​
 =T 
i
​
 ×P 
UT
​
 =9.900×0,00443≈43,9 người

# 4. Methodology
## 4.1 Notation and Data Inputs
## 4.2 Model Structure
## 4.3 Probability Distribution of Trip Lengths


4.2. Probability Distribution of Trip Lengths: Cách bạn xử lý các bin khoảng cách.
4.3. The Proposed Estimation Model: Trình bày các công thức toán học $T_{ij}$.
4.4. Evaluation Metrics: Các chỉ số như CPC, RMSE, $R^2$.
5. Results (Kết quả)Model Performance: So sánh ma trận ước lượng với Ground truth qua biểu đồ Heatmap hoặc Scatter plot.Spatial Analysis: Phân tích xem mô hình dự báo đúng/sai ở những khu vực nào (ví dụ: khu vực trung tâm CBD vs. Ngoại ô).Sensitivity Analysis: (Nếu có) Thử nghiệm xem việc thay đổi kích thước bin ảnh hưởng thế nào đến kết quả.
6. Discussion (Thảo luận)Interpretation: Giải thích tại sao mô hình lại đạt kết quả như vậy.Implications: Ý nghĩa của kết quả này đối với nhà quản lý giao thông Singapore.Limitations: Những hạn chế (ví dụ: chưa xét đến yếu tố thời gian thực hoặc phương tiện di chuyển cụ thể).
7. Conclusion (Kết luận)Tóm tắt ngắn gọn các phát hiện chính.Đề xuất hướng phát triển tương lai (Future work).
<!-- 8. References (Tài liệu tham khảo)Trình bày theo chuẩn (thường là APA hoặc IEEE tùy tạp chí). -->
# 8. References
1. M. Lenormand, A. Bassolas, and J. J. Ramasco, "Systematic comparison of trip distribution laws and models," J. Transp. Geogr., vol. 51, pp. 158–169, 2016
2. J. Wang, X. Kong, F. Xia, and L. Sun, "Urban Human Mobility: Data-Driven Modeling and Prediction," ACM SIGKDD Explor. Newsl., vol. 21, no. 1, pp. 1–19, 2019
3. M. Luca, G. Barlacchi, B. Lepri, and L. Pappalardo, "A Survey on Deep Learning for Human Mobility," ACM Comput. Surv., vol. 55, no. 1, pp. 1–44, 2021
4. T. T. Vu, N. V. A. Vu, H. P. Phung, and L. D. Nguyen, "Enhanced urban functional land use map with free and open-source data," Int. J. Digit. Earth, vol. 14, no. 11, pp. 1744–1757, 2021
5. C. Rong, J. Feng, and J. Ding, "GODDAG: Generating Origin-Destination Flow for New Cities Via Domain Adversarial Training," IEEE Trans. Knowl. Data Eng., vol. 35, no. 10, pp. 10048–10057, 2023
6. Y. Liu et al., "Representation learning for geospatial data," Annals of GIS, vol. 31, no. 3, 2025
7. Y. Xu, S. Gao, and F. Zhang, "Predicting human mobility flows in cities using deep learning on satellite imagery," Nat. Commun., vol. 16, 2025
8. C. M. Alis, E. F. Legara, and C. Monterola, "Generalized radiation model for human migration," Sci. Rep., vol. 11, 2021
9. H. Wang et al., "Similarity based city data transfer framework in urban digitization," Sci. Rep., vol. 15, p. 10776, 2025
10. R. Gallotti et al., "Distorted insights from human mobility data," Commun. Phys., 2024
11. K. S. Atwal, T. Anderson, D. Pfoser, and A. Züfle, "Commuting flow prediction using OpenStreetMap data," Comput. Urban Sci., vol. 5, no. 2, pp. 1–14, 2025
12. F. Simini, M. C. González, A. Maritan, and A.-L. Barabási, "A universal model for mobility and migration patterns," Nature, vol. 484, no. 7392, pp. 96–100, 2012
13. X. Liang, J. Zhao, L. Dong, and K. Xu, "Unraveling the origin of exponential law in intra-urban human mobility," Sci. Rep., vol. 3, p. 2983, 2013
14. A. Noulas, S. Scellato, R. Lambiotte, M. Pontil, and C. Mascolo, "A tale of many cities: Universal patterns in human urban mobility," PLoS ONE, vol. 7, p. e37027, 2012