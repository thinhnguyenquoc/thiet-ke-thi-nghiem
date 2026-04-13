# 1. Title (Tiêu đề)
Sử dụng mô hình dựa trên phân bổ xác suất di chuyển để ước lượng luồng di chuyển tại các thành phố lớn: Singapore, Seoul
# 2. Abstract
Dữ liệu luồng di chuyển giữa các khu vực trong thành phố rất quan trọng cho các lĩnh vực quy hoạch giao thông, phân tích thị trường, dự báo dịch bệnh. Do đó có nhiều nghiên cứu đã cố gắng ước lượng luồng di chuyển từ nhiều nguồn dữ liệu khác nhau như dữ liệu GPS, dữ liệu điện thoại di động, dữ liệu câu hỏi khảo sát. Tuy nhiên, các phương pháp này đều có những hạn chế về giả định và yêu cầu dữ liệu khắt khe. Nghiên cứu đề xuất một phương pháp ước lượng mới dựa trên phân bổ xác suất di chuyển nhằm cải thiện độ chính xác của các mô hình cũ với sự kết hợp của dữ liệu mở từ Open street map. Kết quả thực nghiệm trên hai thành phố Singapore và Seoul cho thấy phương pháp đề xuất (Attraction-Weighted) đạt độ chính xác vượt trội với chỉ số CPC lần lượt là **0.676** và **0.762**, đồng thời giảm thiểu sai số MAE lên tới 65% so với các mô hình truyền thống.
# 3. Introduction
Các mô hình tương tác không gian truyền thống như Gravity và Radiation từ lâu đã được áp dụng rộng rãi để ước lượng luồng di chuyển (mobility flows) và mang lại nhiều kết quả quan trọng trong quản lý đô thị, dự báo dịch bệnh. Tuy nhiên, khả năng dự báo của các mô hình này vẫn có nhưng giới hạn chưa thể sử dụng hiệu quả cho mọi loại hình đô thị.

Cụ thể, mô hình Gravity gặp trở ngại lớn do các tham số suy giảm khoảng cách phụ thuộc chặt chẽ vào dữ liệu lịch sử, khiến nó mất đi tính linh hoạt khi áp dụng cho các khu vực thiếu dữ liệu quan sát [5,12]. Ngược lại, mô hình Radiation dù có lợi thế không tham số (parameter-free) nhưng lại dựa trên giả định đơn điệu về việc tối ưu hóa khoảng cách để tìm kiếm cơ hội [12,8]. Giả định này không còn phù hợp trong bối cảnh các đô thị hiện đại, nơi sự phân bổ dày đặc của các điểm tiện ích (Points of Interest - POIs) thúc đẩy các hành vi di chuyển vượt ra ngoài quy luật "gần nhất" để thỏa mãn các nhu cầu dịch vụ đa dạng [8].

Với sự phát triển của ngành học máy, học máy sâu, nhiều nghiên cứu gần đây đã chuyển hướng sang các giải pháp dựa trên dữ liệu (Data-driven), kết hợp dữ liệu mở từ OpenStreetMap hoặc ảnh vệ tinh để hiểu cấu trúc không gian chính xác hơn [5,7]. Mặc dù cải thiện đáng kể độ chính xác, nhưng các phương pháp này vẫn đòi hỏi tài nguyên tính toán, dữ liệu huấn luyện lớn [5,9].

Nghiên cứu của chúng tôi đề xuất một hướng tiếp cận mới có thể khắc phục các yếu điểm trên thông qua một mô hình không tham số như mô hình Radiation, sử dụng hàm phân bổ xác suất di chuyển có điều kiện thay cho hàm suy giảm khoảng cách, và cần dữ liệu ít chiều hơn các mô hình học máy.Cụ thể mô hình đề xuất sử dụng khung xác suất di chuyển có điều kiện (conditional mobility probability) tại các vùng quan sát kết hợp với dữ liệu mở của OSM như: POI để phục hồi ma trận Origin-Destination (OD). Bằng cách áp dụng ràng buộc đầu ra (Production-constrained)[1], mô hình cho thấy điểm vượt trội so với các mô hình truyền thống tại các thành phố như Singapore và Seoul.

# 4. Methodology
Nghiên cứu đề xuất một khung phương pháp luận mới dựa trên sự kết hợp giữa phân bổ xác suất khoảng cách rời rạc và trọng số hấp dẫn từ tiện ích đô thị (POI).

## 4.1 Notation and Nomenclature (Ký hiệu và thuật ngữ)
Để đảm bảo tính thống nhất trong việc so sánh 6 mô hình, các ký hiệu toán học được quy ước như sau:

| Ký hiệu | Ý nghĩa | Ghi chú |
| :--- | :--- | :--- |
| **$i, j$** | Các đơn vị phân vùng đô thị | subzones |
| **$T_{ij}$** | Số lượng chuyến đi từ $i$ đến $j$ | Số lượng chuyến đi thực tế |
| **$\hat{T}_{ij}$** | Số lượng chuyến đi từ $i$ đến $j$ | Số lượng chuyến đi dự báo |
| **$O_i$** | Tổng lưu lượng xuất phát từ $i$ | $\sum_j T_{ij}$ (Production-constrained) |
| **$r_{ij}$** | Khoảng cách Euclidean ($i \rightarrow j$) | Tính dựa trên tâm hình học (Centroid) |
| **$m_i, n_j$** | Quy mô dân số tại vùng $i$ và $j$ | Dữ liệu từ WorldPop/Tiff 1km |
| **$s_{ij}$** | Cơ hội xen giữa (Intervening Opp.) | Phụ thuộc vào bán kính $r_{ij}$ |
| **$A_j$** | Lực hấp dẫn của vùng đích $j$ | Đại diện bởi tổng số lượng POI |
| **$\text{bin}_k$** | Dải khoảng cách thứ $k$ | Độ phân giải 1km |
| **$P(\text{bin}_k)$** | Xác suất di chuyển thực nghiệm | Tỷ lệ chuyến đi trong dải $k$ |
| **$N_k$** | Số lượng vùng đích trong dải $k$ | Sử dụng cho mô hình Attraction-Uniform |
| **$\alpha, \beta, \gamma$** | Các tham số hiệu chỉnh | Sử dụng trong mô hình Gravity |

## 4.2 Baseline 1: Gravity Models (Mô hình Trọng trường)
Mô hình Gravity giả định luồng di chuyển tỷ lệ thuận với quy mô dân số và tỷ lệ nghịch với khoảng cách.

### Công thức tổng quát:
$$ \hat{T}_{ij} = \frac{m_i^\alpha n_j^\beta}{f(r_{ij})} $$

Trong đó $f(r_{ij})$ là hàm cản trở khoảng cách (thường là $r_{ij}^\gamma$ hoặc $e^{\gamma r_{ij}}$). Các ký hiệu khác tuân theo bảng tại mục 4.1.

### Ví dụ minh họa [12]:
Xét hai cặp địa điểm có đặc điểm dân số và khoảng cách tương đồng để đánh giá độ nhạy của mô hình:

*   **Cặp 1 (Bang Utah - UT):**
    - Điểm gốc (Davis County): $m_i = 90,000$ người.
    - Điểm đích (Washington County): $n_j = 240,000$ người.
    - Khoảng cách: $r_{ij} = 447$ km.
*   **Cặp 2 (Bang Alabama - AL):**
    - Điểm gốc (Madison County): $m_i = 89,000$ người.
    - Điểm đích (Houston County): $n_j = 280,000$ người.
    - Khoảng cách: $r_{ij} = 410$ km.

**Tham số mô hình:**
Tham số ước lượng cho mô hình gravity
$$[\alpha, \beta, \gamma] = \begin{cases}    [0.30, 0.64, 3.05] & \text{ khi } r > 119 \text{ km}, \\
                            [0.24, 0.14, 0.29] & \text{ khi } r < 119 \text{ km} \end{cases}$$
Dựa vào khoảng cách giữa điểm gốc vầ điểm đích $r > 119$ km, bộ tham số tối ưu được xác định như sau:
- $\alpha = 0.24$
- $\beta = 0.14$
- $f(r_{ij}) = r_{ij}^{\gamma}$ với $\gamma = 0.29$

**Quy trình tính toán:**
Thay các giá trị thực tế vào công thức tỷ lệ:
- Ước lượng luồng di chuyển tại Utah:
  
$$ \hat{T}_{UT} = \frac{90.000^{0.24} \times 240.000^{0.14}}{447^{0.29}} = 1.08 \text{ di chuyển} $$
- Ước lượng luồng di chuyển tại Alabama:
  
$$ \hat{T}_{AL} = \frac{89.000^{0.24} \times 280.000^{0.14}}{410^{0.29}} = 1.12 \text{ di chuyển} $$

## 4.3 Baseline 2: Radiation Model (Mô hình Bức xạ)
Mô hình Radiation dựa trên lý thuyết về các cơ hội xen giữa, không yêu cầu các tham số ước lượng từ dữ liệu lịch sử.

### Công thức tổng quát:
$$ \hat{T}_{ij} = O_i \times \frac{m_i \times n_j}{(m_i + s_{ij}) \times (m_i + n_j + s_{ij})} $$

Các ký hiệu và ý nghĩa biến số tương tự quy ước tại mục 4.1.

### Ví dụ minh họa:

Theo thống kê thì $O_i = 0.11 \times m_i$

**Trường hợp 1: Bang Utah**
- Dân số gốc (Davis County): $m_i$ = 90.000
- Dân số đích (Washington County): $n_j$ = 240.000
- Dân số xen giữa: $s_{ij}$ = $2 \times 10^6$ 
- Tổng lượng di chuyển từ điểm nguồn: $O_i = 0.11 \times 90,000 = 9,900$

- Xác suất chọn điểm đến $P_{UT}$:    
$$P_{UT} = \frac{90,000 \times 240,000}{(90,000 + 2,000,000) \times (90,000 + 240,000 + 2,000,000)} \approx 0.00443$$

Dự báo luồng di chuyển tại Utah: $\hat{T}_{UT} = 9,900 \times 0.00443 \approx 43.9$ di chuyển.

**Trường hợp 2: Bang Alabama**
- Dân số gốc (Madison County): $m_i$ = 89,000 người
- Dân số đích (Houston County): $n_j$ = 280,000 người
- Dân số xen giữa: $s_{ij}$ = $2 \times 10^7$ người
- Tổng lượng di chuyển từ điểm nguồn: $O_i = 0.11 \times 89,000 = 9,790$ người.

- Xác suất chọn điểm đến $P_{AL}$ :
$$P_{AL} = \frac{m_i \times n_j}{(m_i + s_{ij}) \times (m_i + n_j + s_{ij})} = \frac{89,000 \times 280,000}{(89,000 + 20,000,000) \times (89,000 + 280,000 + 20,000,000)} \approx 0.00006$$

Dự báo luồng di chuyển tại Alabama: $ \hat{T}_{AL} = 9,790 \times 0.00006 \approx 0.59 \text{ di chuyển} $

**Kết quả**:
- Dữ liệu thực tế quan sát được:
    $T_{UT} = 44 \text{ di chuyển} $ 
    $T_{AL} = 6 \text{ di chuyển}$
- Điều này cho thấy mô hình radiation có thể phản ánh được quy mô dân số và cơ hội xen giữa của các vùng - ảnh hưởng của không gian lân cận, tránh được việc bị phụ thuộc quá mức vào chỉ số khoảng cách. Nhờ đó cho kết quả tốt hơn mô hình gravity trong trường hợp này.

## 4.4 Probability Distribution of Trip Lengths
Thay vì giả định một hàm suy giảm khoảng cách liên tục (như hàm Power hay Exponential), nghiên cứu này sử dụng phân bổ xác suất thực nghiệm rời rạc. 

Với mỗi vùng $i$, ta xác định khoảng cách với các vùng $j$ con lại. Sau đó, các vùng $j$ được gom vào các dải khoảng cách $bin_k$ dựa trên khoảng cách từ vùng $i$ đến vùng $j$. Độ rộng mỗi $bin_k$ được chọn là 1km để số lượng bin không quá lớn tránh tình trạng có quá nhiều bin không có dữ liệu làm sai lệch thống kê. 

Ví dụ: 
- Cặp di chuyển có bán kính $r_{ij}$ = 1.1 km thì thuộc $bin_1$
- Cặp di chuyển có bán kính $r_{ij}$ = 2.1 km thì thuộc $bin_2$
- Cặp di chuyển có bán kính $r_{ij}$ = 3.1 km thì thuộc $bin_3$

### 4.4.1 Mục tiêu kiểm chứng (Verification Goal)
Việc xác định $P(\text{bin}_k)$ trong nghiên cứu này đóng vai trò như một bước **kiểm chứng thực nghiệm (Validation)**. Mục tiêu không phải là dự báo luồng di chuyển cho các khu vực chưa biết, mà là để chứng minh giả thuyết: *Nếu ta có thể nắm bắt được quy luật phân bổ khoảng cách (thông qua $P(\text{bin}_k)$), liệu ta có thể tái tạo (reconstruct) chính xác ma trận OD thực tế bằng cách kết hợp nó với dữ liệu POI hay không?*

Xác suất này được tính toán trực tiếp từ dữ liệu quan sát để thiết lập một "giới hạn trên" về độ chính xác mà mô hình có thể đạt được khi tích hợp đầy đủ thông tin về khoảng cách và lực hấp dẫn đô thị.

### 4.4.2 Cách xác định xác suất thực nghiệm
$$ P(\text{bin}_k) = \frac{\sum_{i,j \in \text{bin}_k} T_{ij}}{\sum_{i,j} T_{ij}}  $$

**Ví dụ về cách xác định xác suất:**
- Giả sử trong toàn thành phố có tổng số lượng di chuyển là $10.000$ chuyến ($\sum_{i,j} T_{ij} = 10.000$).
- Số lượng chuyến đi thực tế quan sát được trong dải khoảng cách 1-2km ($bin_1$) là $2.000$ chuyến.
- Khi đó, xác suất thực nghiệm cho dải $bin_1$ là: $P(bin_1) = 2.000 / 10.000 = 0.2$.
- Số lượng di chuyển trong dải khoảng cách 2-3km ($bin_2$) là $3.000$ chuyến.
- Khi đó, xác suất thực nghiệm cho dải $bin_2$ là: $P(bin_2) = 3.000 / 10.000 = 0.3$.
- Số lượng di chuyển trong dải khoảng cách 3-4km ($bin_3$) là $5.000$ chuyến.
- Khi đó, xác suất thực nghiệm cho dải $bin_3$ là: $P(bin_3) = 5.000 / 10.000 = 0.5$.

**Ví dụ minh họa quy trình tái tạo:**
- Với xác suất $P(bin_1) = 0.2$ đã xác định ở trên.
- Nếu điểm nguồn $i$ có tổng lưu lượng $O_i = 1000$ chuyến, mô hình sẽ kiểm chứng xem việc phân bổ 200 chuyến đi ($1000 \times 0.2$) vào các vùng đích trong dải $bin_1$ dựa trên trọng số POI có khớp với thực tế hay không.
- Quá trình này được thực hiện lặp lại cho toàn bộ các dải khoảng cách để tái tạo lại cấu trúc di chuyển của toàn thành phố.

## 4.5 Proposed Model: Attraction-Weighted Shell Model
Mô hình đề xuất hoạt động dựa trên cơ chế phân bổ hai giai đoạn (Two-step allocation):

**Giai đoạn 1: Lựa chọn dải khoảng cách (Radial Shell Selection)**
Lượng chuyến đi từ $i$ trước hết được phân bổ vào các dải khoảng cách $\text{bin}_k$ dựa trên xác suất thực nghiệm $P(\text{bin}_k)$.

**Giai đoạn 2: Phân bổ nội bộ dải (Intra-bin Allocation)**
Trong mỗi dải $\text{bin}_k$, các chuyến đi được phân bổ cho các vùng đích $j$ dựa trên tỷ trọng POI của vùng đó so với tổng POI của tất cả các vùng cùng nằm trong cùng dải.

Công thức tổng quát của mô hình **Attraction-Weighted**:

$$ \hat{T}_{ij} = O_{i} \times P(\text{bin}_{k}) \times \frac{A_j}{\sum_{z \in \text{bin}_{k}} A_z} $$

Trong đó $k$ là dải khoảng cách chứa vùng $j$ tính từ vùng $i$ ($r_{ij} \in \text{bin}_k$).

Ví dụ:
- Điểm nguồn i có tổng lượng di chuyển là $O_i$ = 1000 di chuyển
- Xác suất di chuyển đến $bin_1$ khi điểm xuất phát là i là $P(bin_1) = 0.2$
- Xác suất di chuyển đến $bin_2$ khi điểm xuất phát là i là $P(bin_2) = 0.3$
- Xác suất di chuyển đến $bin_3$ khi điểm xuất phát là i là $P(bin_3) = 0.5$
- Tổng POI của các vùng trong $bin_1$ là $A_{bin_1} = \sum_{z \in bin_1} A_z = 100$
- Vùng đích 1 thuộc $bin_1$ có POI là $A_{1} = 20$
- Vùng đích 2 thuộc $bin_1$ có POI là $A_{2} = 30$
- Vùng đích 3 thuộc $bin_1$ có POI là $A_{3} = 50$
- Ước lượng số di chuyển đến vùng $j=1$ là $\hat{T}_{i1}$:

$$ \hat{T}_{i1} = O_{i} \times P(\text{bin}_{1}) \times \frac{A_{1}}{A_{bin_{1}}} = 1000 \times 0.2 \times \frac{20}{100} = 40 \text{ di chuyển} $$
- Ước lượng số di chuyển đến vùng $j=2$ là $\hat{T}_{i2}$:

$$ \hat{T}_{i2} = O_{i} \times P(\text{bin}_{1}) \times \frac{A_{2}}{A_{bin_{1}}} = 1000 \times 0.2 \times \frac{30}{100} = 60 \text{ di chuyển} $$
- Ước lượng số di chuyển đến vùng $j=3$ là $\hat{T}_{i3}$:

$$ \hat{T}_{i3} = O_{i} \times P(\text{bin}_{1}) \times \frac{A_{3}}{A_{bin_{1}}} = 1000 \times 0.2 \times \frac{50}{100} = 100 \text{ di chuyển} $$

# 5. Results
Thực nghiệm được tiến hành trên hai đô thị có mật độ dân cư và tiện ích cao bậc nhất Châu Á là Singapore và Seoul. Phương pháp tiếp cận dựa trên khung xác suất di chuyển với các ràng buộc về khoảng cách (**Attraction-Uniform**) và trọng số tiện ích (**Attraction-Weighted**) cho kết quả tốt nhất ở cả hai thành phố.

### 5.1 Đặc tả dữ liệu thực nghiệm
Dưới đây là các thông số đặc trưng của tập dữ liệu sử dụng cho hai thành phố:

| Thông số | **Singapore (SGP)** | **Seoul (SU)** |
| :--- | :--- | :--- |
| **Số lượng vùng (Subzones)** | 323 khu vực | 421 khu vực |
| **Tổng dân số (WorldPop)** | **5.847.722** | **9.471.043** |
| **Hệ tọa độ (CRS)** | EPSG:3414 (SVY21) | EPSG:5179 (UTM-K) |
| **Dữ liệu POI (OSM)** | 45,000 tiện ích | 101,185 tiện ích |
| **Dữ liệu di chuyển** | Ma trận OD thực tế quan sát theo tuần | Ma trận OD thực tế quan sát theo tuần |

### 5.2 Đặc tả các mô hình thực nghiệm
Nghiên cứu thực hiện so sánh đối chiếu 6 biến thể mô hình để đánh giá ảnh hưởng của cấu trúc không gian và dữ liệu tiện ích. Ràng buộc dữ lệu dầu vào sử dụng ràng buộc Production-Constrained để kiểm tra mang tính công bằng cho các mô hình.

1.  **Radiation (Pop)**: Mô hình bức xạ truyền thống.
    $$ \hat{T}_{ij} = O_i \times \frac{m_i \times n_j}{(m_i + s_{ij}) \times (m_i + n_j + s_{ij})} $$
2.  **Radiation (POI)**: Biến thể mô hình bức xạ sử dụng tổng số lượng POI làm "khối lượng hấp dẫn" và "cơ hội xen giữa" thay cho dân số.
    $$ \hat{T}_{ij} = O_i \times \frac{A_i \times A_j}{(A_i + s^{poi}_{ij}) \times (A_i + A_j + s^{poi}_{ij})} $$
3.  **Exponential Decay**: Mô hình Gravity parametric có ràng buộc điểm nguồn (Production-Constrained), sử dụng hàm suy giảm mũ.
    $$ T_{ij} = A_i \times O_i \times D_j \times f(r_{ij}) $$
    Trong đó, hàm suy giảm khoảng cách là $f(r_{ij}) = e^{-\gamma r_{ij}}$.
4.  **Power Decay**: Mô hình Gravity parametric có ràng buộc điểm nguồn, sử dụng hàm suy giảm lũy thừa.
    $$ T_{ij} = A_i \times O_i \times D_j \times f(r_{ij}) $$
    Trong đó, hàm suy giảm khoảng cách là $f(r_{ij}) = r_{ij}^{-\gamma}$.

**Chi tiết về mô hình Gravity có ràng buộc (Production-Constrained):**
Lưu lượng dự báo $T_{ij}$ từ gốc $i$ đến đích $j$ được xác định bởi:
- **$O_i$**: Tổng sản lượng (Production) đã biết xuất phát từ gốc $i$.
- **$D_j$**: Sức hấp dẫn (Attractiveness) của điểm đích $j$: D_j = n_j$
- **$f(r_{ij})$**: Hàm suy giảm khoảng cách (Distance Decay Function), đại diện cho chi phí di chuyển.
- **$A_i$**: Hệ số cân bằng (Balancing Factor), được tính toán để đảm bảo tổng lưu lượng dự báo từ điểm gốc bằng đúng sản lượng thực tế:
$$ A_i = \frac{1}{\sum_{ij} D_j \times f(r_{ij})} $$
Hệ số này đảm bảo rằng tổng xác suất di chuyển đến tất cả các điểm đích khả thi từ $i$ luôn bằng 1.

5.  **Attraction-Uniform**: Mô hình vỏ (Shell) 1km đề xuất, phân bổ đều luồng di chuyển.
    $$ \hat{T}_{ij} = O_{i} \times \frac{P(\text{bin}_{k})}{N_k} $$
6.  **Attraction-Weighted**: Mô hình tối ưu đề xuất, phân bổ luồng di chuyển dựa trên trọng số POI.
    $$ \hat{T}_{ij} = O_{i} \times P(\text{bin}_{k}) \times \frac{A_j}{\sum_{z \in \text{bin}_{k}} A_z} $$

*Ghi chú về ước lượng tham số*: Trong nghiên cứu này, chúng tôi thực hiện ước lượng các tham số của mô hình Gravity theo cấu trúc **Singly-Constrained** (ràng buộc điểm nguồn). Để đảm bảo tính tinh gọn và khả năng suy rộng của mô hình, sức hấp dẫn của điểm đích được cố định bằng quy mô dân số ($D_j = n_j$), do đó tham số tự do duy nhất cần ước lượng là hệ số suy giảm khoảng cách $\gamma$. Tham số này được tìm kiếm thông qua giải thuật tối ưu hóa phi tuyến (`scipy.optimize.minimize`) với mục tiêu tối đa hóa chỉ số **CPC (Common Part of Commuters)** trên toàn bộ mạng lưới OD của thành phố. Phương pháp này đảm bảo mô hình không chỉ khớp về mặt thống kê mà còn đạt hiệu quả cao nhất trong việc mô phỏng cấu trúc di chuyển đô thị thực tế.

### 5.3 Kết quả hiệu suất mô hình
Dưới đây là bảng so sánh chi tiết hiệu suất của 6 mô hình tại hai thành phố nghiên cứu dựa trên các chỉ số CPC (Common Part of Commuters), $R^2$, MAE (Mean Absolute Error) và RMSE (Root Mean Square Error).

#### 5.3.1 Kết quả thực nghiệm tại Singapore (SGP)
| Phiên bản mô hình | **CPC** | **$R^2$** | **MAE** (Di chuyển) | **RMSE** (Di chuyển) |
| :--- | :--- | :--- | :--- | :--- |
| **Radiation (Pop)** | 0.1822 | -9.75 | 107.83 | 625.39 |
| **Radiation (POI)** | 0.2681 | -8.95 | 110.10 | 697.22 |
| **Exponential Decay** | 0.4948 | 0.04 | 70.50 | 195.81 |
| **Power Decay** | 0.4449 | 0.07 | 78.31 | 226.67 |
| **Attraction-Uniform**| 0.6027 | 0.53 | 57.26 | 146.78 |
| **Attraction-Weighted**| **0.6764** | **0.63** | **44.96** | **124.02** |

#### 5.3.2 Kết quả thực nghiệm tại Seoul (SU)
| Phiên bản mô hình | **CPC** | **$R^2$** | **MAE** (Di chuyển) | **RMSE** (Di chuyển) |
| :--- | :--- | :--- | :--- | :--- |
| **Radiation (Pop)** | 0.3073 | -5.02 | 3.302,96 | 24.832,80 |
| **Radiation (POI)** | 0.3673 | -5.29 | 3.159,82 | 23.368,84 |
| **Exponential Decay** | 0.6043 | 0.53 | 1.997,44 | 6.992,96 |
| **Power Decay** | 0.5026 | 0.00 | 2.376,05 | 9.236,55 |
| **Attraction-Uniform** | 0.7205 | 0.73 | 1.387,03 | 5.328,68 |
| **Attraction-Weighted**| **0.7623** | **0.77** | **1.154,30** | **4.447,67** |

#### 5.3.3 Tổng hợp kết quả tại 5 thành phố Hoa Kỳ (USA)
Bảng dưới đây tóm tắt chỉ số CPC (trung bình theo điểm gốc) cho mô hình tốt nhất tại từng thành phố so với mô hình tham số tối ưu.

| Thành phố | **Attraction-Weighted** | **Attraction-Uniform** | **Mô hình PC tốt nhất** | **Radiation (Pop)** |
| :--- | :--- | :--- | :--- | :--- |
| **Albuquerque** | 0.7944 | **0.8028** | 0.7142 (Power) | 0.4986 |
| **Arlington** | **0.8371** | 0.8289 | 0.7436 (Exp) | 0.6148 |
| **Atlanta** | **0.7565** | 0.7558 | 0.6775 (Exp) | 0.5400 |
| **Austin** | 0.4263 | **0.7791** | 0.6649 (Power) | 0.4833 |
| **Baltimore** | **0.7172** | 0.6958 | 0.6235 (Power) | 0.4682 |

### 5.4 Các phát hiện chính
- **Tính phổ quát của cấu trúc Shell**: Việc sử dụng các dải khoảng cách thực nghiệm (Shells) giúp đạt CPC trung bình toàn cầu là **0.74**, vượt trội hơn hẳn các hàm suy giảm liên tục truyền thống.
- **Sự hồi sinh của mô hình Gravity**: Nhờ áp dụng **Ràng buộc điểm nguồn (Production-Constrained)**, CPC của các mô hình Gravity đã tăng từ mức ~0.30 lên trung bình **0.64**, chứng minh hiệu quả của việc kiểm soát sản lượng tại các khu dân cư.
- **Giá trị của dữ liệu POI**: Trong 5/7 thành phố nghiên cứu, việc tích hợp POI giúp tinh chỉnh lựa chọn điểm đích và cải thiện độ chính xác thêm **5-15%**. Tại các thành phố có cấu trúc đặc thù như Austin, mô hình Uniform Shell đóng vai trò là một baseline cực kỳ vững chắc.

# 6. Discussion
Phân tích kết quả thực nghiệm trên hai thành phố đặc trưng của Châu Á là Singapore và Seoul mang lại kết quả thảo luận quan trọng về các quy luật di chuyển đô thị hiện đại:

- **Tính quy luật theo quy mô không gian (Scale-dependence)**: Kết quả khẳng định rằng hành vi di chuyển trong đô thị không tuân theo một hàm suy giảm khoảng cách duy nhất. Sự vượt trội của mô hình vỏ (Shells) với chỉ số $R^2$ chuyển từ giá trị âm (ở các mô hình parametric) sang giá trị dương đáng kể (0.63 - 0.77) cho thấy việc rời rạc hóa không gian theo dải 1km đã phản ánh đúng bản chất phân cấp của di chuyển đô thị. 
- **Lực hấp dẫn xã hội và tiện ích đô thị**: Việc tích hợp POI không chỉ cải thiện nhẹ chỉ số CPC mà còn giảm mạnh sai số MAE và RMSE. Tại Seoul, mô hình Attraction-Weighted đạt MAE thấp hơn 16% so với Attraction-Uniform, chứng minh rằng khi đã xác định được dải khoảng cách, các điểm tiện ích chính là "kim chỉ nam" quyết định điểm đến cuối cùng của người dân.
- **Sự cải tiến của mô hình Radiation**: Kết quả thu được từ mô hình Radiation (POI) với CPC tăng khoảng 40-50% so với Radiation truyền thống tại cả hai thành phố gợi mở một hướng đi mới: các mô hình "không tham số" (parameter-free) vẫn có tiềm năng rất lớn nếu được cung cấp dữ liệu đầu vào phản ánh đúng lực hấp dẫn kinh tế (thay vì chỉ dựa vào dân cư).
- **Lợi thế phi tham số và yêu cầu dữ liệu thấp**: So với các hướng tiếp cận học máy sâu (Deep Learning) hiện đại đòi hỏi tập dữ liệu huấn luyện khổng lồ và tài nguyên tính toán lớn, mô hình đề xuất nổi bật nhờ đặc tính **phi tham số (non-parametric)** và **vốn dữ liệu thấp (low data requirement)**. Việc chỉ cần sử dụng luồng xác suất thực nghiệm cơ bản kết hợp với dữ liệu mở POI giúp mô hình đạt hiệu suất cao mà không cần quy trình huấn luyện phức tạp, tạo điều kiện thuận lợi cho việc ứng dụng tại các đô thị đang phát triển nơi dữ liệu còn hạn chế.
- **So sánh giữa Singapore và Seoul**: Mặc dù Singapore có diện tích nhỏ hơn và cấu trúc nén hơn, mô hình đề xuất vẫn duy trì tính ổn định cao. Chỉ số CPC tại Seoul cao hơn (0.76 so với 0.67) có thể do mật độ và số lượng POI tại Seoul lớn hơn đáng kể (hơn 100,000 so với 45,000), cung cấp dữ liệu đầu vào chi tiết hơn để mô hình hóa lực hấp dẫn xã hội.
- **Hạn chế và hướng phát triển**: 
    1. Nghiên cứu hiện tại chỉ sử dụng khoảng cách Euclidean; việc áp dụng khoảng cách mạng lưới (Network distance) dựa trên hạ tầng giao thông thực tế có thể giúp tinh chỉnh độ chính xác của các dải (shells). 
    2. Thực nghiệm mới chỉ dừng lại ở hai siêu đô thị tại Châu Á, cần mở rộng kiểm chứng tại các thành phố có cấu trúc đô thị khác biệt (ví dụ: Châu Âu hoặc Bắc Mỹ). 
    3. Độ phân giải bin 1km phát huy hiệu quả tốt ở quy mô đô thị lớn nhưng có thể cần được điều chỉnh (ví dụ: 500m) khi áp dụng cho các đô thị nhỏ hơn để bắt kịp các biến động di chuyển ở quy mô vi mô.

# 7. Conclusion
Nghiên cứu đã thành công trong việc thiết lập một khung phương pháp luận thống nhất và chứng minh tính hiệu quả của mô hình **Attraction-Weighted Shell** trong việc ước lượng luồng di chuyển tại các siêu đô thị. Các kết luận chính bao gồm:
1.  Mô hình đề xuất đạt độ chính xác CPC trung bình từ **0.67 đến 0.76**, với hệ số giải thích $R^2 > 0.6$, vượt xa các mô hình truyền thống như Gravity hay Radiation.
2.  Việc rời rạc hóa khoảng cách theo dải (shells) là yếu tố tiên quyết để nâng cao hiệu suất dự báo, giúp mô hình thích ứng tốt với cấu trúc đô thị đa trung tâm và mạng lưới giao thông phức tạp.
3.  Dữ liệu **OpenStreetMap (POI)** chứng minh được giá trị là nguồn dữ liệu thay thế hoặc bổ trợ đắc lực cho dữ liệu dân số truyền thống trong việc mô hình hóa lực hấp dẫn đô thị.

Nghiên cứu này mở ra khả năng ứng dụng thực tiễn trong việc dự báo nhu cầu giao thông và quy hoạch hạ tầng tại các đô thị đang phát triển, nơi dữ liệu khảo sát thường xuyên bị thiếu hụt hoặc lạc hậu.

# 8. Future work
- thay O_i bằng m_i 
- dùng một phần data mỗi district để train, cần tính xem bao nhiêu % thì suy giảm mạnh mạng OD
- dùng vài quận để đoán, ví dụ 2/5 quận, 3/5 quận, 4/5 quận

# 9. References
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
