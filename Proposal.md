<!-- 1. Title (Tiêu đề)Nên chứa: Phương pháp chính + Đối tượng nghiên cứu + Địa điểm.Ví dụ: "Inferring Intra-city Mobility Flows from Sparse Observations: A Distance-based Probability Approach in Singapore." -->
# 1. Title (Tiêu đề)
Sử dụng mô hình dựa trên phân bổ xác suất di chuyển để ước lượng luồng di chuyển tại các thành phố lớn: Singapre, Seoul
<!-- 2. Abstract (Tóm tắt)Context: Tầm quan trọng của dữ liệu OD trong quy hoạch đô thị.Gap: Hạn chế của các phương pháp cũ (ví dụ: thiếu dữ liệu ground truth hoặc mô hình Gravity quá đơn giản).Method: Giới thiệu mô hình bạn sử dụng (Origin-constrained, Distance-based bins).Key Results: Kết quả đạt được (ví dụ: CPC đạt bao nhiêu, RMSE giảm bao nhiêu %). -->
# 2. Abstract
Dữ liệu luồng di chuyển giữa các khu vực trong thành phố rất quan trọng cho các lĩnh vực quy hoạch giao thông, phân tích thị trường, dự báo dịch bệnh. Do đó có nhiều nghiên cứu đã cố gắng ước lượng luồng di chuyển từ nhiều nguồn dữ liệu khác nhau như dữ liệu GPS, dữ liệu điện thoại di động, dữ liệu câu hỏi khảo sát. Tuy nhiên, các phương pháp này đều có những hạn chế về giả định và yêu cầu dữ liệu khắt khe. Nghiên cứu đề xuất một phương pháp ước lượng mới dựa trên phân bổ xác suất di chuyển nhằm cải thiện độ chính xác của các mô hình cũ với sự kết hợp của dữ liệu mở từ Open street map. Kết quả đạt được ...
<!-- 3. Introduction (Dẫn nhập)Problem Statement: Tại sao việc ước lượng luồng di chuyển tại Singapore lại quan trọng?Literature Review: Tóm tắt các nghiên cứu trước đây về Spatial Interaction Models (Gravity, Radiation).Contribution: Nêu rõ 2-3 điểm mới của bài báo (Ví dụ: Sử dụng xác suất di chuyển thực tế từ dữ liệu mới). -->
# 3. Introduction
Các mô hình truyền thông như gravity, radiation luôn được áp dụng rộng rãi để để ước lượng luồng di chuyển giữa các khu vực địa lý và đã mang lại nhiều kết quả thành công.Tuy nhiên tuỳ thuộc vào các kiểu dữ liệu và đặc điểm của khu vực mà các mô hình này có những hạn chế khác nhau. 
Có thể kết luận rằng mô hình gravity có nhược điểm là thông số được ước lượng từ dữ liệu đã được cung cấp theo lịch sử hoặc thu thập nên khó áp dụng cho vùng thiếu dữ liệu[5,12]. Mô hình radiation thì có giả định đơn điệu là mọi người ưu tiên đi gần nhất để kiếm công việc, cơ hội hơn là cố gắng đi xa hơn để hưởng các tiện ích khác[12,8]. Điều này chưa phù hợp với các siêu đô thị nơi có số lượng tiện ích rất lớn và người dân di chuyển nhiều để sử dụng các tiện ích này.[8]
Các giải pháp khắc phục chính để cải thiện yếu điểm này là thay thế dần việc chỉ sử dụng dân số là chỉ số đánh giá và kinh tế xã hội. Nghiên cứu mô hình bức xạ tổng quát (Generalized Radiation Model) sử dụng thông tin về POI, dân số, mật độ dân số để làm thước đo mới[8]. Các phương pháp machine learning học nhiều đặc tính của các khu vực quan sát thông qua nhiều thuộc tính dữ liệu, cũng như sử dụng ảnh vệ tinh để học cấu trúc không gian[5,7]. Tuy nhiên các phương pháp học sâu và máy học này vẫn đòi hỏi dữ liệu lớn nhiều chiều và khó chuyển đổi (transfer) cho các khu vực ít dữ liệu do phụ thuộc vào lượng lớn nhãn huấn luyện.[5,9]
Nghiên cứu của chúng tôi sử dụng xác suất di chuyển có điều kiện của một người tại một khu vực cụ thể kết hợp dữ liệu POI để phục hồi luồng di chuyển khi biết tổng số lượng di chuyển đi ra (outflows) từ một khu vực của các siêu đô thị như Singapore, Seoul (thường tỉ lệ thuận với dân số)[13,14,15]. Hướng tiếp cận ràng buộc đầu ra (Production Constrained) này mang lại một hướng nghiên cứu mới khắc phục sự yếu thế của mô hình radiation vì giả định tối ưu hoá việc ít di chuyển trong môi trường siêu đô thị đa tiện ích là rất hạn chế.[5,7,14]

## 3.1 Traditrional Spatial Interaction Models
- Mô hình Gravity:
    giớ hạn: [Semini2012] khung lý thuyết Cực đại hóa Entropy (Wilson, 1967) cho thấy khi kiểm tra ở entropy cực đại thì alpha, Beta gần về 1, nhưng hàm suy giảm khoảng cách không biết là theo làm mũ hay hàm e mũ. chưa có thực nghiệm hay lý thuyết nào để làm cơ sở chọn hàm suy giảm phù hợp. Khi đưa qua các kkhu vực ít thông tin về giao thông thì ước lượng alpha beta bị hạn chế.
- Mô hình Radiation
## 3.2 Data-driven approaches
- Mô hình deep gravity 
- Thu giảm số trường dữ liệu cần bằng cách học từ dữ liệu mở OpenStreetMap
<!-- # 4. Methodology (Phương pháp nghiên cứu)Đây là phần quan trọng nhất mà mình đã dự thảo cho bạn ở trên. Cần chia nhỏ thành: -->
# 4. Methodology
<!-- 4.1. Study Area and Data Sources: Mô tả về các Zone của Singapore, dữ liệu luồng Out-flow và dữ liệu Ground truth. -->
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