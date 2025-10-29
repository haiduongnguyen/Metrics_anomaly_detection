# VPBank Technology Hackathon 2025

## Tổng Quan

Đội 36 – Opstimus đề xuất giải pháp Phát hiện Bất thường Chỉ số và Phân tích Nguyên nhân Gốc rễ được hỗ trợ bởi AI, được thiết kế để nâng cao tính ổn định và khả năng vận hành chủ động của các hệ thống số quy mô lớn trong lĩnh vực ngân hàng và thương mại điện tử. Giải pháp kết hợp mô hình thống kê với các thuật toán học máy để phát hiện bất thường theo thời gian thực với độ chính xác cao, đồng thời tích hợp lớp lý luận AI được hỗ trợ bởi AWS Bedrock để phân tích dữ liệu hệ thống, xác định nguyên nhân gốc rễ và đề xuất các hành động khắc phục. Thông qua cơ chế cảnh báo thông minh và phản hồi tự động, hệ thống giúp các đội DevOps giảm đáng kể Thời gian Trung bình để Giải quyết (MTTR), giảm thiểu thời gian ngừng hoạt động và tiến tới mô hình vận hành AIOps thích ứng.

## Bài Toán Thách Thức

Phát hiện bất thường chỉ số và AI phân tích nguyên nhân gốc rễ

## Tên Đội

Đội 36 - Opstimus

---

## Thành Viên Đội

| Họ và Tên | Vai trò | Địa chỉ Email | Trường | Chuyên ngành | LinkedIn |
|-----------|---------|---------------|---------|--------------|----------|
| Nguyễn Hải Dương | Trưởng nhóm | haiduong66799@gmail.com | HUST | Data – Machine learning | https://www.linkedin.com/in/nguyen-hai-duong-1a34a71ba/ |
| Phạm Đỗ Huy Thành | Thành viên | phamdohuythanh@gmail.com | University Of Greenwich | Computer Science | N/A |
| Lê Thành Sơn | Thành viên | lethanhson9901@gmail.com | HUST | N/A | N/A |
| Ngân Hà | Thành viên | toanhoc011235813213455@gmail.com | HUST | N/A | N/A |
| Trương Đức Thắng | Thành viên | truongducthang30112002@gmail.com | HCMUS | N/A | https://www.linkedin.com/in/tdthang/ |

---

## Mục Lục

- Giới thiệu Giải pháp
- Tác động của Giải pháp
- Đi sâu vào Giải pháp
- Kiến trúc Giải pháp

---

## Giới Thiệu Giải Pháp

Trong bối cảnh số hóa ngày nay, đặc biệt trong các tổ chức ngân hàng và tài chính, các hệ thống doanh nghiệp đang trở nên ngày càng phức tạp, kết nối chặt chẽ và có quy mô lớn. Việc phát hiện sớm các bất thường trong các hệ thống này đã trở thành yếu tố then chốt để đảm bảo tính ổn định, bảo mật và trải nghiệm khách hàng liền mạch.

Các công cụ giám sát truyền thống như Prometheus và Grafana chủ yếu tập trung vào thu thập và trực quan hóa dữ liệu, trong khi khả năng xác định và phân tích nguyên nhân gốc rễ của các bất thường vẫn phụ thuộc rất nhiều vào sự diễn giải của con người. Sự phụ thuộc này dẫn đến số lượng cảnh báo sai quá nhiều hoặc bỏ lỡ các sự cố quan trọng, buộc các đội vận hành phải phản ứng thủ công, điều này tốn thời gian, không hiệu quả và dễ xảy ra lỗi.

### Phương Pháp Tiếp Cận Của Chúng Tôi

Đội 36 – Opstimus giới thiệu giải pháp được thiết kế đặc biệt để vượt qua những hạn chế này thông qua việc phát triển hệ thống phát hiện bất thường chỉ số gần thời gian thực.

Hệ thống tích hợp các phương pháp thống kê với các mô hình học máy (ML) để đảm bảo độ chính xác, tốc độ và khả năng thích ứng trong nhiều môi trường vận hành khác nhau. Nó tuân theo kiến trúc bốn lớp: Thu thập & Xử lý, Phát hiện & Phân tích Nguyên nhân Gốc rễ, Cảnh báo, và Vòng lặp Phản hồi, tạo thành một chu trình khép kín cho phép học tập liên tục và tự cải thiện dựa trên dữ liệu vận hành thực tế.

**1. Thu thập & Xử lý (Ingestion & Processing)**

Lớp này chịu trách nhiệm thu thập, tổng hợp và xử lý các chỉ số từ nhiều nguồn như hạ tầng hệ thống, cơ sở dữ liệu, ứng dụng và các sự kiện vận hành. Dữ liệu chỉ số được xử lý ở chế độ streaming để duy trì khả năng phản hồi thời gian thực. Trong quá trình thu thập, dữ liệu được làm sạch, chuẩn hóa và lưu trữ tạm thời để chuẩn bị cho việc phát hiện và phân tích bất thường.

**2. Phát hiện & Phân tích Nguyên nhân Gốc rễ (Detection & Root Cause Analysis)**

Đây là lớp cốt lõi của giải pháp. Hệ thống áp dụng các phương pháp thống kê (ví dụ: Z-score, phân tách STL, IQR) cùng với các mô hình học máy (ví dụ: Random Cut Forest, SR-CNN) để phát hiện các mẫu bất thường trong chỉ số theo thời gian thực. Sau khi phát hiện bất thường, hệ thống tự động phân tích các nguyên nhân gốc rễ tiềm năng dựa trên bối cảnh vận hành như tăng đột biến lưu lượng, thay đổi cấu hình hoặc các sự kiện kinh doanh cụ thể. Phương pháp kết hợp này giúp giảm cảnh báo dương tính giả và cung cấp thông tin chi tiết có thể hành động, phong phú về ngữ cảnh để khắc phục sự cố nhanh hơn.

**3. Cảnh báo (Alerting)**

Lớp Cảnh báo đảm bảo rằng thông báo đến đúng người, đúng thời điểm và với đúng ngữ cảnh. Nó tích hợp liền mạch với các công cụ quản lý sự cố được sử dụng rộng rãi như Slack, PagerDuty hoặc Jira, cung cấp thông tin chi tiết về mức độ nghiêm trọng, nguyên nhân gốc rễ có thể xảy ra và các hành động khắc phục được đề xuất. Cơ chế này cho phép các đội kỹ thuật phản ứng nhanh hơn và giảm đáng kể cả Thời gian Trung bình để Phát hiện (MTTD) và Thời gian Trung bình để Giải quyết (MTTR).

**4. Vòng lặp Phản hồi (Feedback Loop)**

Vòng lặp Phản hồi đóng vai trò quan trọng trong việc cho phép hệ thống học hỏi và phát triển theo thời gian. Mọi phản hồi từ người vận hành như xác nhận liệu cảnh báo có chính xác hay không, cập nhật nguyên nhân thực tế hoặc xem xét các mẫu lịch sử đều được hệ thống ghi lại. Các đầu vào này được sử dụng để tinh chỉnh ngưỡng phát hiện, huấn luyện lại các mô hình ML và nâng cao độ chính xác phát hiện trong các chu kỳ tiếp theo. Kết quả là, hệ thống trở nên ngày càng thông minh và thích ứng hơn, cải thiện khả năng ra quyết định với mỗi lần lặp.

### Kết Luận

Với kiến trúc như trên, xử lý dữ liệu gần thời gian thực và độ chính xác phát hiện cao, giải pháp được đề xuất bởi Đội 36 – Opstimus cho phép các tổ chức chủ động phát hiện rủi ro vận hành và tự động hóa việc giám sát và phân tích hệ thống.

---

## Tác Động Của Giải Pháp

### 2.1. Tác Động Xã Hội và Đối Tượng Mục Tiêu

Giải pháp phát hiện và phân tích bất thường thông minh của chúng tôi không chỉ cải thiện hiệu quả vận hành hệ thống mà còn tạo ra các tác động tích cực rộng lớn hơn cho cả doanh nghiệp và cộng đồng công nghệ.

| Khía cạnh | Tác động Cụ thể |
|-----------|-----------------|
| Vận hành Hệ thống | Giảm thời gian ngừng hoạt động, đảm bảo tính ổn định và độ tin cậy 24/7 cho các dịch vụ ngân hàng và tài chính. |
| Trải nghiệm Người dùng | Duy trì chất lượng dịch vụ cao và giảm thiểu gián đoạn trong các giao dịch trực tuyến và hoạt động tài chính. |
| Lực lượng Kỹ thuật | Giảm áp lực lên các đội DevSecOps. AI hỗ trợ phát hiện, giải thích và đề xuất các hành động khắc phục, cho phép các kỹ sư tập trung vào đổi mới thay vì khắc phục sự cố phản ứng. |
| Tác động Kinh tế & Tài chính | Giảm thiểu thiệt hại doanh thu do ngừng hoạt động. Một giờ hệ thống gián đoạn có thể dẫn đến thiệt hại hàng trăm triệu VNĐ. Giải pháp rút ngắn Thời gian Trung bình để Giải quyết (MTTR) từ hàng giờ xuống chỉ còn vài phút. |

### 2.2. Ưu Điểm So Với Các Giải Pháp Hiện Có

| Tiêu chí | Giải pháp Truyền thống (Grafana, Prometheus, …) | Giải pháp Đề xuất |
|----------|--------------------------------------------------|-------------------|
| Phương pháp Phát hiện | Dựa trên cảnh báo theo quy tắc và ngưỡng cố định | Kết hợp các mô hình ensemble dựa trên quy tắc, ML và thống kê để phát hiện thích ứng theo thời gian thực |
| Khả năng Phân tích | Hiển thị dữ liệu; yêu cầu giải thích của con người | AI tự động phân tích nguyên nhân gốc rễ và đề xuất các hành động khắc phục |
| Cảnh báo Dương tính Giả | Tỷ lệ cao, dẫn đến mệt mỏi cho các đội vận hành | Ensemble đa lớp giảm cả dương tính giả và âm tính giả |
| Nhận thức Bối cảnh Kinh doanh | Không có | Hiểu bối cảnh kinh doanh (sự kiện lịch, Flash Sales, xu hướng xã hội) để tạo cảnh báo phù hợp |
| Mức độ Tự động hóa | Phản ứng và thủ công | Chủ động, dự đoán và tự phục hồi với phản hồi tự động |

### 2.3. Lợi Thế Cạnh Tranh và Điểm Bán Hàng Độc Đáo

**a. Xử lý Dữ liệu Streaming Gần Thời gian Thực**

Hệ thống xử lý hơn hàng nghìn sự kiện mỗi giây với độ trễ dưới 5 giây, được hỗ trợ bởi kiến trúc streaming (Kafka + Kinesis). Lý tưởng cho các tình huống khẩn cấp như tấn công DDoS, rò rỉ bộ nhớ hoặc quá tải cơ sở dữ liệu. Không giống như các hệ thống xử lý theo lô, kiến trúc này cho phép phát hiện bất thường ngay lập tức và hành động thời gian thực trước khi sự cố leo thang.

**b. Hệ thống Học Máy Kết hợp Thông minh**

Giải pháp của chúng tôi áp dụng khung phát hiện bất thường kết hợp bốn lớp, kết hợp các phương pháp phân tích đa dạng để có độ chính xác và độ tin cậy vượt trội.

- **Lớp Thống kê:** STL, IQR và Z-score để nắm bắt tính mùa vụ và độ lệch.
- **Lớp Học Máy:** Random cut tree, SN-CNN và clustering để phát hiện bất thường đa chiều.
- **Lớp Dựa trên Quy tắc:** Cảnh báo cụ thể cho kinh doanh được xác định bởi các chuyên gia lĩnh vực.
- **Phân tích Đồ thị:** Phân tích các phụ thuộc giữa các dịch vụ để xác định các lỗi lan truyền.

Một bất thường chỉ được xác nhận khi hai hoặc nhiều phương pháp đồng ý, nâng cao độ tin cậy và giảm cảnh báo sai. Clustering nhóm các bất thường có tương quan, cho phép tương quan nguyên nhân gốc rễ nhanh chóng và chính xác trên các hệ thống kết nối.

**c. Trực quan hóa Topo theo Thời gian Thực**

Hệ thống tự động tạo bản đồ phụ thuộc dịch vụ trong kiến trúc microservices, cung cấp cái nhìn thời gian thực về cách các thành phần tương tác. Khi xảy ra bất thường, nó làm nổi bật các luồng ngược và xuôi dòng, hiển thị bán kính tác động và phạm vi tác động tiềm năng trên các dịch vụ. Giao diện trực quan hóa tương tác sử dụng mã màu để biểu diễn độ trễ, khối lượng lưu lượng và sức khỏe dịch vụ, cho phép các kỹ sư xác định vị trí và chẩn đoán vấn đề nhanh hơn 3-5 lần so với các phương pháp truyền thống.

**d. Lý luận AI và Tương tác Ngôn ngữ Tự nhiên**

Giải pháp tận dụng AWS Bedrock làm nền tảng cho Lớp Lý luận AI của nó, cho phép hiểu biết theo ngữ cảnh, suy luận nhân quả và tương tác con người-AI tự nhiên.

Các LLM được quản lý của Bedrock (như Anthropic Claude hoặc Amazon Titan) xử lý các tín hiệu kết hợp từ chỉ số, nhật ký và siêu dữ liệu để phân tích bất thường, suy luận nguyên nhân gốc rễ và tạo ra các đề xuất khắc phục với giải thích đầy đủ ngữ cảnh.

Công cụ lý luận được hỗ trợ bởi Bedrock duy trì bộ nhớ hội thoại, hỗ trợ các câu hỏi tiếp theo và liên tục học hỏi từ phản hồi của người vận hành thông qua Vòng lặp Phản hồi. Theo thời gian, nó tinh chỉnh độ chính xác lý luận, hiểu biết ngữ cảnh và sự rõ ràng của các giải thích.

---

## Đi Sâu Vào Giải Pháp

**Hình 1: Kiến trúc tổng thể của giải pháp**

*[Mô tả sơ đồ kiến trúc: Sơ đồ thể hiện luồng dữ liệu từ các nguồn thu thập (CloudWatch Logs, System Metrics, APM Metrics) qua các lớp xử lý chính bao gồm Data Lake (S3 Raw Buckets), lớp ETL (AWS Glue), lớp phát hiện bất thường (Lambda + SageMaker), lớp phân tích nguyên nhân (AWS Bedrock), và cuối cùng là lớp hành động/cảnh báo (SQS + CloudWatch). Các thành phần được kết nối bằng các mũi tên chỉ hướng luồng dữ liệu, với vòng lặp phản hồi quay trở lại để cải thiện hệ thống.]*

### Phân Tích Chi Tiết Các Lớp Hệ Thống

| Lớp Hệ thống | Mô tả Chi tiết |
|--------------|----------------|
| **1. Thu thập Dữ liệu từ Nhiều Nguồn** | Hệ thống liên tục thu thập dữ liệu từ nhiều nguồn khác nhau, bao gồm nhật ký ứng dụng, nhật ký cơ sở dữ liệu, các chỉ số hệ thống (như CPU, bộ nhớ, độ trễ, tỷ lệ lỗi) và các tài liệu vận hành (runbooks và playbooks). Tất cả dữ liệu được đưa vào Lớp Thu thập thông qua Data Lake hoặc Streaming Storage. |
| **2A. Xử lý và Chuẩn hóa Dữ liệu (ETL)** | Trong Lớp Xử lý, hệ thống thực hiện quy trình Trích xuất-Chuyển đổi-Tải (ETL). Nhật ký và chỉ số được làm sạch, đồng bộ hóa thời gian và chuyển đổi thành lược đồ thống nhất để chuẩn bị cho phân tích tiếp theo. |
| **2B. Lưu trữ Dữ liệu và Phân tích Thời gian Thực** | Sau khi xử lý, dữ liệu được lưu trữ trong Data Lake để phân tích lịch sử trong khi đồng thời được truyền đến lớp Streaming Storage để phát hiện bất thường theo thời gian thực. |
| **3. Phát hiện Bất thường qua Rule Engine và Học Máy** | Decision Engine kết hợp hai cơ chế: (1) Rule-based Engine cho cảnh báo ngưỡng tĩnh (ví dụ: CPU > 90%), và (2) mô-đun Phát hiện Bất thường dựa trên ML sử dụng các mô hình như STL + IQR, Random Cut Forest và SR-CNN để nắm bắt các bất thường thời gian phức tạp. |
| **4. Phân tích Nguyên nhân Gốc rễ với Lý luận AI** | Khi phát hiện bất thường, Root Cause Analysis (RCA) Engine được kích hoạt để xác định nguyên nhân gốc rễ của vấn đề. Mô hình Lý luận AI tận dụng các tương quan thời gian, đồ thị phụ thuộc dịch vụ và kiến thức từ các tài liệu vận hành (runbooks/playbooks) để suy luận chuỗi nhân-quả và xác định chính xác thành phần bị lỗi. |
| **5. Cảnh báo và Trực quan hóa Dashboard Thời gian Thực** | Action Layer tự động kích hoạt cảnh báo đến Alert Manager (qua email, Slack hoặc các hệ thống giám sát nội bộ). Đồng thời, tất cả kết quả phân tích được trực quan hóa trên dashboard thời gian thực, cho phép các đội vận hành dễ dàng giám sát sức khỏe hệ thống và truy vết nguyên nhân gốc rễ. |
| **6. Học tập và Vòng lặp Phản hồi** | Sau khi giải quyết sự cố, kết quả được ghi lại để cho phép hệ thống tự học: cập nhật ngưỡng quy tắc, mở rộng bộ dữ liệu huấn luyện cho các mô hình ML và tự động làm phong phú runbooks và playbooks với các quy trình xử lý mới. Vòng lặp phản hồi liên tục này cho phép nâng cao trí thông minh hệ thống dần dần. |

---

## Kiến Trúc Giải Pháp

### Luồng Bất thường từ Mỗi Node

*[Mô tả sơ đồ luồng bất thường: Sơ đồ chi tiết hiển thị cách các bất thường được phát hiện và xử lý từ từng node trong hệ thống. Bắt đầu từ các metrics sources (CPU, Memory, Latency, Error Rate), dữ liệu đi qua các bộ phát hiện khác nhau (Statistical Detection với STL+IQR, ML Detection với Random Cut Forest và SR-CNN, Rule-based Detection). Kết quả từ các bộ phát hiện này được tổng hợp tại Decision Engine, nơi áp dụng voting mechanism để xác nhận bất thường. Sau đó, thông tin được chuyển đến RCA Engine để phân tích nguyên nhân và cuối cùng đến Alert Manager để gửi thông báo.]*

*[Sơ đồ tiếp tục thể hiện chi tiết về service dependency graph, cho thấy cách hệ thống theo dõi mối quan hệ giữa các microservices. Khi một service bị bất thường, hệ thống tự động xác định các services upstream và downstream bị ảnh hưởng, tính toán blast radius và hiển thị trên topology visualization với mã màu chỉ báo mức độ nghiêm trọng.]*

### Xếp hạng với Vòng lặp Phản hồi Con người và Clustering Lỗi để Phát hiện Nguyên nhân Gốc rễ trong Mỗi Node

*[Mô tả sơ đồ ranking và clustering: Sơ đồ minh họa cơ chế xếp hạng các bất thường dựa trên độ nghiêm trọng, tần suất xuất hiện và phản hồi lịch sử từ người vận hành. Hệ thống sử dụng thuật toán clustering (như DBSCAN hoặc K-means) để nhóm các bất thường có tương quan với nhau, giúp xác định các incident patterns phổ biến. Vòng lặp phản hồi được thể hiện qua luồng dữ liệu từ operator feedback quay trở lại để cập nhật scoring weights và retrain clustering models. Mỗi cluster được gán một confidence score và được liên kết với các known root causes từ knowledge base.]*

### Streaming và Lưu trữ Metrics Sẵn sàng cho Phân tích

*[Mô tả sơ đồ streaming metrics: Sơ đồ kiến trúc streaming pipeline chi tiết, bắt đầu từ các data producers (applications, infrastructure, databases) gửi metrics đến Kafka/Kinesis streams. Dữ liệu được xử lý qua stream processing layer (có thể là Kinesis Data Analytics hoặc Flink) để thực hiện các phép tính aggregation, windowing và filtering theo thời gian thực. Sau đó, dữ liệu được lưu trữ song song vào hai đích: (1) Hot storage (ElastiCache/Redis) cho truy vấn thời gian thực với TTL ngắn, và (2) Cold storage (S3) cho lưu trữ dài hạn và phân tích batch. Time-series database như TimeStream hoặc InfluxDB cũng có thể được sử dụng cho việc truy vấn metrics theo thời gian hiệu quả.]*

### Xử lý Batch để Lưu trữ Ngữ cảnh Tài liệu và Kiến trúc từ Confluence

*[Mô tả sơ đồ batch processing: Sơ đồ thể hiện quy trình ETL batch để trích xuất và xử lý dữ liệu từ Confluence. Bắt đầu với scheduled jobs (AWS Glue hoặc Lambda) kích hoạt định kỳ để crawl Confluence pages thông qua REST API. Dữ liệu được trích xuất bao gồm runbooks, playbooks, architecture diagrams và operational procedures. Sau đó, dữ liệu trải qua các bước: (1) Text extraction và parsing, (2) Metadata enrichment (tags, timestamps, authors), (3) Document embedding sử dụng transformer models để tạo vector representations, (4) Storage vào vector database (như Pinecone, Weaviate hoặc OpenSearch) để hỗ trợ semantic search. Knowledge graph cũng được xây dựng để biểu diễn mối quan hệ giữa các concepts, services và procedures.]*

### Kết hợp và Tóm tắt Lý luận

*[Mô tả sơ đồ reasoning combination: Sơ đồ minh họa cách AWS Bedrock tổng hợp thông tin từ nhiều nguồn để tạo ra phân tích nguyên nhân gốc rễ toàn diện. Input signals bao gồm: (1) Anomaly scores từ ML models, (2) Log snippets từ affected services, (3) Metric time-series data, (4) Service dependency graph, (5) Historical incident data, và (6) Relevant documentation từ knowledge base. Bedrock LLM (Claude hoặc Titan) xử lý các signals này thông qua multi-step reasoning process: correlation analysis, temporal pattern matching, causal inference, và context synthesis. Output bao gồm: (1) Root cause explanation với confidence level, (2) Contributing factors được xếp hạng theo mức độ ảnh hưởng, (3) Recommended remediation steps với priority, và (4) Similar historical incidents để tham khảo. Reasoning process cũng generate natural language summary dễ hiểu cho operators.]*

### Sơ đồ Luồng Đầy đủ của Chúng tôi

*[Mô tả sơ đồ luồng tổng thể end-to-end: Sơ đồ tích hợp toàn bộ các thành phần đã mô tả ở trên thành một luồng xử lý hoàn chỉnh. Bắt đầu từ Data Sources (Applications, Infrastructure, Databases) → Ingestion Layer (CloudWatch, Kafka/Kinesis) → Processing Layer (AWS Glue ETL, Stream Processing) → Storage Layer (S3 Data Lake với raw/transformed buckets, Hot/Cold storage) → Detection Layer (Statistical + ML + Rule-based engines chạy song song) → Decision Engine (Voting mechanism và anomaly confirmation) → Root Cause Analysis Engine (AWS Bedrock reasoning với knowledge base integration) → Action Layer (Alert Manager, Dashboard Visualization) → Feedback Loop (Operator input, Model retraining, Knowledge base updates). Các luồng dữ liệu được phân biệt bằng màu sắc: real-time streaming (màu xanh), batch processing (màu cam), feedback loops (màu tím). Mỗi component được gán nhãn rõ ràng với AWS service tương ứng và có chỉ số performance metrics như latency, throughput.]*

---

## Các Dịch vụ AWS Được Sử dụng trong Hệ thống

### a. Các Dịch vụ AWS Được Sử dụng

Giải pháp của chúng tôi được xây dựng hoàn toàn trên các dịch vụ gốc của AWS, đảm bảo khả năng mở rộng cao, bảo mật mạnh mẽ và vận hành đơn giản hóa.

**CloudWatch Logs / Metrics**

Thu thập nhật ký hệ thống, chỉ số hệ thống và chỉ số APM theo thời gian thực. Dữ liệu được truyền đến Amazon S3 (Raw Logs / Raw Metrics / Raw APM Metrics) để lưu trữ dài hạn và truy vấn thống nhất.

**Amazon S3 (Data Lake: Raw → Transformed)**

Đóng vai trò là xương sống dữ liệu của hệ thống. Các buckets Raw nhận dữ liệu chưa xử lý, sau khi ETL được chuyển đổi thành các phân vùng lược đồ chuẩn hóa (theo thời gian và dịch vụ) trong bucket transformed—sẵn sàng cho phân tích và suy luận ML.

**AWS Glue (ETL + Data Catalog)**

Chạy các công việc ETL để làm sạch, chuẩn hóa và phân vùng dữ liệu. Tất cả các lược đồ được đăng ký trong Glue Data Catalog, cho phép truy cập nhất quán cho Athena, Redshift Spectrum và các mô hình ML.

**AWS Lambda (Rule-based Detection & Orchestration)**

Thực thi các luồng phát hiện dựa trên quy tắc để xác định vi phạm ngưỡng theo thời gian thực. Điều phối pipeline triggers các công việc ETL, gọi các endpoints suy luận ML và đẩy sự kiện đến SQS và CloudWatch.

**Amazon SageMaker (ML Training & Inference)**

Huấn luyện và triển khai các mô hình như STL + IQR, SR-CNN và Random Cut Forest để phát hiện bất thường chỉ số. Các mô hình này được công khai thông qua SageMaker Endpoints, cho phép Decision Engine thực hiện chấm điểm bất thường theo thời gian thực.

**Amazon Bedrock (AI Reasoning)**

Sử dụng các Mô hình Ngôn ngữ Lớn (LLMs) để suy luận nguyên nhân gốc rễ từ các tín hiệu ML và log kết hợp. Tham khảo kiến thức vận hành được lưu trữ trong S3 (runbooks và playbooks) để tạo ra các giải thích theo ngữ cảnh và các hành động khắc phục được đề xuất.

**Amazon SQS + CloudWatch (Action / Alerting)**

SQS tổng hợp các cảnh báo từ nhiều nguồn và định tuyến chúng dựa trên mức độ nghiêm trọng, trong khi CloudWatch Alarms và Dashboards trực quan hóa các chỉ số theo thời gian thực và kích hoạt thông báo cảnh báo thông qua các kênh tích hợp.

### b. Tích hợp và Tương tác của Các Dịch vụ AWS

Luồng dữ liệu end-to-end (như được minh họa trong sơ đồ kiến trúc) tích hợp tất cả các thành phần AWS một cách liền mạch:

**1. Lớp Thu thập (Ingestion Layer)**

CloudWatch thu thập Logs, System Metrics và APM Metrics và ghi chúng vào S3 Raw Buckets (ba danh mục). Athena hoặc Redshift Spectrum có thể truy vấn trực tiếp dữ liệu thô cho các cuộc điều tra và phân tích ad-hoc.

**2. Lớp Xử lý (Processing Layer)**

Glue Jobs xử lý và chuẩn hóa dữ liệu thô, lưu trữ kết quả trong S3 Transformed Buckets (Logs / Metrics / APM). Glue Catalog cung cấp các lược đồ thống nhất trên tất cả các khối lượng công việc phân tích và ML.

**3. Decision Engine**

Lambda thực thi phát hiện dựa trên quy tắc theo thời gian thực. Song song, Lambda gọi SageMaker Endpoints để chấm điểm bất thường đa phương pháp. Kết quả được hợp nhất theo dịch vụ và timestamp để tương quan tiếp theo.

**4. Root Cause Analysis Engine**

Bedrock nhận các tín hiệu đầu vào (bất thường chỉ số, đoạn log, metadata) và thực hiện lý luận nguyên nhân gốc rễ, tạo ra các giải thích và các bước khắc phục. Nó tham khảo các runbooks được lưu trữ trong S3 để đảm bảo đầu ra có thể hành động và nhận thức ngữ cảnh.

**5. Action Layer**

Các cảnh báo được gửi đến SQS để ưu tiên và định tuyến, sau đó được trực quan hóa trên CloudWatch Dashboards. Các cảnh báo cũng có thể được chuyển tiếp đến các kênh phản ứng sự cố nội bộ (ví dụ: email, Slack hoặc hệ thống ticketing).

**6. Feedback Loop**

Kết quả sự cố được lưu trữ trong S3 / Glue và được sử dụng để định kỳ huấn luyện lại các mô hình ML và điều chỉnh ngưỡng quy tắc trên SageMaker. Điều này tạo ra một vòng lặp tự học, cho phép hệ thống liên tục cải thiện độ chính xác và khả năng phản ứng của nó.