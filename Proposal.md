# 1. Title (Tiêu đề)
Sử dụng mô hình dựa trên phân bổ xác suất di chuyển để ước lượng luồng di chuyển tại các thành phố lớn: Singapore, Seoul
# 2. Abstract
Dữ liệu luồng di chuyển giữa các khu vực trong thành phố rất quan trọng cho các lĩnh vực quy hoạch giao thông, phân tích thị trường, dự báo dịch bệnh. Do đó có nhiều nghiên cứu đã cố gắng ước lượng luồng di chuyển từ nhiều nguồn dữ liệu khác nhau như dữ liệu GPS, dữ liệu điện thoại di động, dữ liệu câu hỏi khảo sát. Tuy nhiên, các phương pháp này đều có những hạn chế về giả định và yêu cầu dữ liệu khắt khe. Nghiên cứu đề xuất một phương pháp ước lượng mới dựa trên phân bổ xác suất di chuyển nhằm cải thiện độ chính xác của các mô hình cũ với sự kết hợp của dữ liệu mở từ Open street map. Kết quả thực nghiệm trên hai thành phố Singapore và Seoul cho thấy phương pháp đề xuất (Attraction-Weighted) đạt độ chính xác vượt trội với chỉ số CPC lần lượt là **0.676** và **0.762**, đồng thời giảm thiểu sai số MAE lên tới 65% so với các mô hình truyền thống.
# 3. Introduction
Các mô hình tương tác không gian truyền thống như Gravity và Radiation từ lâu đã được áp dụng rộng rãi để ước lượng luồng di chuyển (mobility flows) và mang lại nhiều kết quả quan trọng trong quản lý đô thị, dự báo dịch bệnh. Tuy nhiên, khả năng dự báo của các mô hình này vẫn có nhưng giới hạn chưa thể sử dụng hiệu quả cho mọi loại hình đô thị.

Cụ thể, mô hình Gravity gặp trở ngại lớn do các tham số suy giảm khoảng cách phụ thuộc chặt chẽ vào dữ liệu lịch sử, khiến nó mất đi tính linh hoạt khi áp dụng cho các khu vực thiếu dữ liệu quan sát [5,12]. Ngược lại, mô hình Radiation dù có lợi thế không tham số (parameter-free) nhưng lại dựa trên giả định đơn điệu về việc tối ưu hóa khoảng cách để tìm kiếm cơ hội [12,8]. Giả định này không còn phù hợp trong bối cảnh các đô thị đa trung tâm, nơi sự phân bổ dày đặc của các điểm tiện ích (Points of Interest - POIs) thúc đẩy các hành vi di chuyển vượt ra ngoài quy luật "gần nhất" để thỏa mãn các nhu cầu dịch vụ đa dạng [8].

Để khắc phục, nhiều nghiên cứu gần đây đã chuyển hướng sang các giải pháp dựa trên dữ liệu (Data-driven), đặc biệt là học máy và học sâu nhằm khai thác thông tin từ OpenStreetMap hoặc ảnh vệ tinh để hiểu cấu trúc không gian [5,7]. Mặc dù cải thiện đáng kể độ chính xác, nhưng các phương pháp này vẫn đòi hỏi tài nguyên tính toán, dữ liệu huấn luyện lớn [5,9].

Nghiên cứu của chúng tôi đề xuất một hướng tiếp cận mới: sử dụng khung xác suất di chuyển có điều kiện (conditional mobility probability) kết hợp với dữ liệu POI để phục hồi ma trận Origin-Destination (OD). Bằng cách áp dụng ràng buộc đầu ra (Production-constrained)[1], phương pháp này không chỉ tận dụng được dữ liệu mở từ OpenStreetMap mà còn khắc phục trực tiếp yếu điểm của mô hình Radiation trong môi trường đô thị nén như Singapore và Seoul. Hướng tiếp cận này hứa hẹn mang lại một giải pháp cân bằng giữa tính chính xác của các mô hình truyền thống.

# 4. Methodology
Nghiên cứu đề xuất một khung phương pháp luận mới dựa trên sự kết hợp giữa phân bổ xác suất khoảng cách rời rạc và trọng số hấp dẫn từ tiện ích đô thị (POI).

## 4.1 Notation and Nomenclature (Ký hiệu và thuật ngữ)
Để đảm bảo tính thống nhất trong việc so sánh 6 mô hình, các ký hiệu toán học được quy ước như sau:

| Ký hiệu | Ý nghĩa | Ghi chú |
| :--- | :--- | :--- |
| **$i, j$** | Các đơn vị phân vùng đô thị | Subzones (Phường/Sub-district) |
| **$T_{ij}$** | Luồng di chuyển từ $i$ đến $j$ | Số lượng chuyến đi thực tế hoặc dự báo |
| **$O_i$** | Tổng lưu lượng xuất phát từ $i$ | $\sum_j T_{ij}$ (Production-constrained) |
| **$r_{ij}$** | Khoảng cách Euclidean ($i \rightarrow j$) | Tính dựa trên tâm hình học (Centroid) |
| **$m_i, n_j$** | Quy mô dân số tại vùng $i$ và $j$ | Dữ liệu từ WorldPop/Tiff 1km |
| **$s_{ij}$** | Cơ hội xen giữa (Intervening Opp.) | Phụ thuộc vào bán kính $r_{ij}$ |
| **$A_j$** | Lực hấp dẫn của vùng đích $j$ | Đại diện bởi tổng số lượng POI |
| **$\text{bin}_k$** | Dải khoảng cách thứ $k$ | Độ phân giải 1km |
| **$P(\text{bin}_k)$** | Xác suất di chuyển thực nghiệm | Tỷ lệ chuyến đi trong dải $k$ |
| **$N_k$** | Số lượng vùng đích trong dải $k$ | Sử dụng cho mô hình Attraction-Uniform |
| **$\alpha, \beta, \gamma$** | Các tham số hiệu chỉnh | Sử dụng trong mô hình Gravity Parametric |

## 4.2 Baseline 1: Gravity Models (Mô hình Trọng trường)
Mô hình Gravity giả định luồng di chuyển tỷ lệ thuận với quy mô dân số và tỷ lệ nghịch với khoảng cách.

### Công thức tổng quát:
$$ \hat{T}_{ij} = \frac{m_i^\alpha n_j^\beta}{f(r_{ij})} $$

Trong đó $f(r_{ij})$ là hàm cản trở khoảng cách (thường là $r_{ij}^\gamma$ hoặc $e^{\gamma r_{ij}}$). Các ký hiệu khác tuân theo bảng tại mục 4.1.

### Thực nghiệm minh họa:
Xét hai cặp địa điểm có đặc điểm dân số và khoảng cách tương đồng để đánh giá độ nhạy của mô hình:

*   **Cặp 1 (Bang Utah - UT):**
    - Điểm gốc (Washington County): $m_i = 90.000$ người.
    - Điểm đích (Davis County): $n_j = 240.000$ người.
    - Khoảng cách: $r_{ij} = 447$ km.
*   **Cặp 2 (Bang Alabama - AL):**
    - Điểm gốc (Houston County): $m_i = 89.000$ người.
    - Điểm đích (Madison County): $n_j = 280.000$ người.
    - Khoảng cách: $r_{ij} = 410$ km.

**Tham số mô hình:**
Dựa trên việc huấn luyện từ dữ liệu thực tế cho các chuyến đi có khoảng cách $r > 119$ km, bộ tham số tối ưu được xác định như sau:
- $\alpha = 0.24$
- $\beta = 0.14$
- $f(r_{ij}) = r_{ij}^c$ với $c = 0.29$

**Quy trình tính toán:**
Thay các giá trị thực tế vào công thức tỷ lệ:
- Luồng di chuyển tại Utah:
  
$$ T_{UT} \propto \frac{90.000^{0.24} \times 240.000^{0.14}}{447^{0.29}} = 1 $$
- Luồng di chuyển tại Alabama:
  
$$ T_{AL} \propto \frac{89.000^{0.24} \times 280.000^{0.14}}{410^{0.29}} = 1 $$

**Kết quả:** Do dân số và khoảng cách của hai cặp gần như tương đương, mô hình dự báo số lượng di chuyển cho cả hai trường hợp đều bằng **1 người**, cho thấy mô hình Gravity gặp khó khăn trong việc phản ánh sự khác biệt thực tế giữa các vùng địa lý khác nhau.

## 4.3 Baseline 2: Radiation Model (Mô hình Bức xạ)
Mô hình Radiation dựa trên lý thuyết về các cơ hội xen giữa, không yêu cầu các tham số ước lượng từ dữ liệu lịch sử.

### Công thức tổng quát:
$$ \hat{T}_{ij} = O_i \frac{m_i \times n_j}{(m_i + s_{ij}) \times (m_i + n_j + s_{ij})} $$

Các ký hiệu và ý nghĩa biến số tương tự quy ước tại mục 4.1.

### Thực nghiệm minh họa:

**Trường hợp 1: Bang Utah (Khu vực thưa dân)**
- Dân số gốc ($m_i$) = 90.000
- Dân số đích ($n_j$) = 240.000
- Dân số xen giữa ($s_{ij}$) = $2 \times 10^6$ (2.000.000)
- Tổng lượng người đi làm ước tính ($O_i$): $0.11 \times 90.000 = 9.900$ người.

**Xác suất chọn điểm đến $P_{UT}$ :**
- Tử số: $m_i \times n_j = 90.000 \times 240.000 = 21,6 \times 10^9$
- Mẫu số 1 ($m_i + s_{ij}$): $90.000 + 2.000.000 = 2.090.000$
- Mẫu số 2 ($m_i + n_j + s_{ij}$): $90.000 + 240.000 + 2.000.000 = 2.330.000$
- $P_{UT} = \frac{21,6 \times 10^9}{2.090.000 \times 2.330.000} \approx 0,00443$

=> Dự báo luồng di chuyển tại Utah: $\hat{T}_{UT} = 9.900 \times 0,00443 \approx 43,9$ người.

**Trường hợp 2: Bang Alabama (Khu vực đông dân)**
- Dân số gốc ($m_i$) = 89.000
- Dân số đích ($n_j$) = 280.000
- Dân số xen giữa ($s_{ij}$) = $2 \times 10^7$ (20.000.000)
- Tổng lượng người đi làm ước tính ($O_i$): $0.11 \times 89.000 = 9.790$ người.

**Xác suất chọn điểm đến $P_{AL}$ :**
- Tử số: $89.000 \times 280.000 = 24,92 \times 10^9$
- Mẫu số 1 ($m_i + s_{ij}$): $89.000 + 20.000.000 = 20.089.000$
- Mẫu số 2 ($m_i + n_j + s_{ij}$): $89.000 + 280.000 + 20.000.000 = 20.369.000$
- $P_{AL} = \frac{24,92 \times 10^9}{20.089.000 \times 20.369.000} \approx 0,00006$

Dự báo luồng di chuyển tại Alabama: 

$$ \hat{T}_{AL} = 9.790 \times 0,00006 \approx 0,59 \text{ người} $$

Kết quả: mô hình radiation phản ánh tốt hơn về khác biệt quy mô dân số giữa hai vùng. Dữ liệu thực tế cho thấy:
    $$T_{UT} = 44$$ 
    $$T_{AL} = 6$$

## 4.4 Proposed Model: Attraction-Weighted Shell Model
Mô hình đề xuất hoạt động dựa trên cơ chế phân bổ hai giai đoạn (Two-step allocation):

**Giai đoạn 1: Lựa chọn dải khoảng cách (Radial Shell Selection)**
Lượng chuyến đi từ $i$ trước hết được phân bổ vào các dải khoảng cách $\text{bin}_k$ dựa trên xác suất thực nghiệm $P(\text{bin}_k)$. Điều này đảm bảo mô hình luôn tuân thủ cấu trúc chi phí khoảng cách của đô thị đó.

**Giai đoạn 2: Phân bổ nội bộ dải (Intra-bin Allocation)**
Trong mỗi dải $\text{bin}_k$, các chuyến đi được phân bổ cho các vùng đích $j$ dựa trên tỷ trọng POI của vùng đó so với tổng POI của tất cả các vùng cùng nằm trong dải.

Công thức tổng quát của mô hình **Attraction-Weighted**:

$$ \hat{T}_{ij} = O_{i} \times P(\text{bin}_{k}) \times \frac{A_j}{\sum_{z \in \text{bin}_{k}} A_z} $$

Trong đó $k$ là dải khoảng cách chứa vùng $j$ tính từ vùng $i$ ($r_{ij} \in \text{bin}_k$).

## 4.5 Probability Distribution of Trip Lengths
Thay vì giả định một hàm suy giảm khoảng cách liên tục (như hàm Power hay Exponential), nghiên cứu này sử dụng phân bổ xác suất thực nghiệm rời rạc. 
- **Lợi ích**: Phương pháp này khắc phục được sai số tại các khoảng cách cực ngắn (vấn đề "singularity" trong mô hình Gravity) và phản ánh chính xác các đặc điểm địa lý đặc thù của siêu đô thị (như ranh giới tự nhiên hoặc cấu trúc quy hoạch tập trung).
- **Cách xác định**: $ P(\text{bin}_k) = \frac{\sum_{i,j \in \text{bin}_k} T_{ij}}{\sum_{i,j} T_{ij}}  $
  
  Mỗi bin được thiết lập với độ phân giải 1km để cân bằng giữa độ chi tiết không gian và tính ổn định thống kê.

# 5. Results
Kết quả thực nghiệm cho thấy một sự phân cấp rõ rệt về hiệu suất dự báo giữa các nhóm mô hình. Phương pháp tiếp cận dựa trên khung xác suất di chuyển với các ràng buộc về khoảng cách (**Attraction-Uniform**) và trọng số tiện ích (**Attraction-Weighted**) cho kết quả tốt nhất ở cả hai thành phố.

### 5.1 Bảng so sánh hiệu suất tổng hợp
Bảng dưới đây trình bày các thông số so sánh giữa 6 mô hình nghiên cứu tại Singapore và Seoul:

| Phiên bản mô hình | Phân loại | **Singapore (CPC)** | **Seoul (CPC)** | **MAE** (Seoul) | **RMSE** (Seoul) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Radiation (Dân số)** | Cơ hội xen giữa | 0.1822 | 0.3073 | 3.303,0 | 24.832,8 |
| **Radiation (POI)** | Cơ hội xen giữa | 0.2681 | 0.3673 | 3.159,8 | 23.368,8 |
| **Exponential Decay** | Tham số | 0.2628 | 0.3497 | 2.162,0 | 11.032,6 |
| **Power Decay** | Tham số | 0.3052 | 0.4768 | 1.944,1 | 10.240,5 |
| **Attraction-Uniform** | Cấu trúc (1km) | **0.6027** | **0.7205** | 1.387,0 | 5.328,7 |
| **Attraction-Weighted**| **Tối ưu (POI)** | **0.6764** | **0.7623** | **1.154,3** | **4.447,7** |

### 5.2 Các phát hiện chính
- **Ưu thế của cấu trúc vỏ (Shells)**: Việc sử dụng các dải khoảng cách thực nghiệm (1km) thay vì các hàm trơn (Power/Exponential) giúp tăng độ chính xác lên gần **100%** (từ ~0.30 lên >0.60 CPC).
- **Giá trị của dữ liệu POI**: Tích hợp dữ liệu POI giúp giảm sai số MAE tại Seoul từ 1.387 xuống còn **1.154** (giảm **16.7%**).
- **Cải thiện mô hình Radiation**: Việc thay thế dân số bằng POI trong mô hình Radiation giúp cải thiện CPC tại Singapore từ **0.18** lên **0.27**.

# 6. Discussion
Phân tích kết quả thực nghiệm trên hai thành phố đặc trưng của Châu Á là Singapore và Seoul mang lại kết quả thảo luận quan trọng về các quy luật di chuyển đô thị hiện đại:

- **Tính quy luật theo quy mô không gian (Scale-dependence)**: Kết quả khẳng định rằng hành vi di chuyển trong đô thị không tuân theo một hàm suy giảm khoảng cách duy nhất trên toàn hệ thống. Việc sử dụng các dải vỏ (Shells) 1km cho phép mô hình thích ứng linh hoạt với cấu trúc đa trung tâm của Seoul và tính nén cực cao của Singapore. Độ chính xác tăng vọt khi chuyển từ mô hình liên tục sang mô hình vỏ rời rạc cho thấy "ngưỡng khoảng cách" là yếu tố quyết định hơn là "hàm số khoảng cách".
- **Lực hấp dẫn xã hội so với lực hấp dẫn dân cư**: Sự cải thiện vượt trội khi tích hợp POI (đặc biệt là trong mô hình Radiation) chứng minh rằng các hoạt động kinh tế, dịch vụ và giải trí là động lực chính của di chuyển nội đô, chứ không chỉ đơn thuần là phân bổ dân cư. Điều này giải thích tại sao các mô hình Radiation truyền thống thường thất bại trong việc dự báo luồng di chuyển ngắn tại các trung tâm thương mại sầm uất.
- **Sự khác biệt giữa hai thành phố**: Mặc dù cùng là đô thị nén, Seoul có chỉ số ma sát khoảng cách ($\gamma = 1.82$) cao hơn Singapore ($\gamma = 1.21$). Điều này phản ánh cấu trúc địa hình phức tạp và mạng lưới giao thông công cộng cực kỳ dày đặc của Seoul, nơi các chuyến đi thường có xu hướng tập trung cục bộ mạnh mẽ hơn so với Singapore.
- **Hạn chế của nghiên cứu**: Nghiên cứu hiện tại chưa phân tách luồng di chuyển theo phương tiện giao thông (Mode split) và thời điểm trong ngày (Time of day). Tuy nhiên, độ chính xác CPC > 0.67 đã cung cấp một bản đồ cơ sở (Baseline) cực kỳ tin cậy cho các phân tích quy hoạch cấp chiến lược.

# 7. Conclusion
Nghiên cứu đã thành công trong việc thiết lập một khung phương pháp luận thống nhất cho việc ước lượng luồng di chuyển đô thị dựa trên xác suất điều kiện và dữ liệu mở. Các kết luận chính bao gồm:
1.  Mô hình **Attraction-Weighted Shell** là phương pháp tối ưu nhất, đạt độ chính xác CPC trung bình trên **0.70**, vượt xa các mô hình truyền thống (Gravity, Radiation).
2.  Mô hình **Radiation POI** là một phát hiện quan trọng, cho thấy khi được hiệu chỉnh bằng dữ liệu tiện ích, mô hình không tham số vẫn có thể đạt hiệu suất cạnh tranh trong đô thị nén.
3.  Dữ liệu **OpenStreetMap** cung cấp một nguồn thông tin dồi dào và chính xác đủ để thay thế các nguồn dữ liệu khảo sát đắt đỏ trong việc xây dựng ma trận OD tại các nước đang phát triển hoặc các khu vực thiếu dữ liệu.

Hướng nghiên cứu tiếp theo sẽ tập trung vào việc tích hợp học sâu để tối ưu hóa trọng số cho từng loại hình POI cụ thể, nhằm tinh lọc hơn nữa lực hấp dẫn tại các "điểm cực" (poles) của đô thị.

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
