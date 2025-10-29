# Kế hoạch Triển khai Hệ thống AI-Powered Metrics Anomaly Detection & Root Cause Analysis (LocalStack → AWS)

## Giới thiệu

**Mục tiêu:**  
\- Xây dựng một hệ thống end-to-end phát hiện bất thường (anomaly detection) và phân tích nguyên nhân gốc rễ (root cause analysis) cho dữ liệu metrics/logs, dựa trên kiến trúc nhiều tầng có tích hợp AI. Hệ thống ban đầu chạy tại môi trường local (dựa trên LocalStack) và sau đó có thể triển khai lên AWS thật.  
\- Thiết kế hệ thống theo hướng modular, dễ mở rộng. Các thành phần AWS không được LocalStack hỗ trợ đầy đủ sẽ có cơ chế **fallback/mocking** tương ứng (ví dụ: dùng service/container giả lập cho Bedrock, SageMaker, ElastiCache, TimeStream, App Mesh).  
\- Đáp ứng yêu cầu vận hành: độ trễ phát hiện bất thường < 5 giây trong bản demo chạy local (POC), đồng thời đưa ra lộ trình nâng cấp lên môi trường AWS thật để đạt các SLA đã đề ra (về hiệu năng, độ tin cậy, v.v.).

**Phạm vi:**  
\- Thiết kế hạ tầng dưới dạng mã (Infrastructure as Code - _IaC_) bằng Terraform, cho phép chuyển đổi dễ dàng giữa môi trường local (LocalStack) và môi trường AWS thật (qua cấu hình biến, provider alias, workspace Terraform).  
\- Kịch bản chạy **local**: Sử dụng tối đa các dịch vụ giả lập của LocalStack (S3, Kinesis, Lambda, SQS, EventBridge, Step Functions, v.v.). Những dịch vụ chưa có trên LocalStack sẽ được mô phỏng bằng container hoặc service thay thế (ví dụ: mô phỏng Bedrock bằng một dịch vụ LLM local, dùng Redis container thay ElastiCache, dùng Neo4j container thay Neptune, v.v.).  
\- Kịch bản chạy **AWS thật**: Sử dụng các dịch vụ AWS managed tương ứng cho toàn bộ pipeline (S3, Kinesis/MSK, Glue, TimeStream hoặc DynamoDB, ElastiCache, SageMaker, Bedrock, Athena, OpenSearch, Neptune/AppMesh...).  
\- **Không đi sâu vào code ứng dụng** mà tập trung vào kiến trúc hạ tầng và các thành phần tích hợp.

**Giả định:**  
\- Có sẵn các tài khoản AWS cho môi trường development/staging/production (sẽ dùng khi chuyển dần từ POC local lên).  
\- Đội ngũ triển khai có quyền quản trị Terraform backend (ví dụ: dùng Terraform Cloud cho giai đoạn local, hoặc S3 + DynamoDB cho state Terraform trên AWS).  
\- Các công cụ tích hợp bên thứ ba như Slack, PagerDuty, Jira đã có môi trường sandbox để kết nối thử nghiệm thông báo sự cố.

**Kết quả kỳ vọng:**  
\- Bộ _Terraform modules_ cho từng lớp của hệ thống (ingestion, ETL, storage, detection, decision, RCA, alerting, feedback, batch knowledge processing, v.v.), có thể tái sử dụng.  
\- Triển khai thành công kịch bản local (LocalStack + các Docker services bổ sung), kiểm thử end-to-end ở mức demo.  
\- Tài liệu hướng dẫn chuyển đổi sang AWS thật theo từng phase, kèm theo các lưu ý về khác biệt và hạn chế giữa môi trường local vs AWS.

## Kiến trúc Tổng quan và Cấu trúc Dự án (Phần 0)

Trước khi đi vào chi tiết từng giai đoạn, dưới đây là cái nhìn tổng quan về kiến trúc hệ thống và cấu trúc dự án, tuân theo các **best practices 2025** trong phát triển hệ thống AIOps:

*   **Kiến trúc phân lớp (Layered Architecture):** Hệ thống được chia thành nhiều lớp chức năng rõ ràng, từ lớp nguồn dữ liệu đến lớp phân tích và phản hồi. Mỗi lớp được triển khai như các module riêng biệt trong Terraform, tuân theo kiến trúc microservices và hướng sự kiện (event-driven). Các lớp chính bao gồm: **Nguồn dữ liệu**, **Tiếp nhận & Streaming**, **Xử lý & ETL**, **Lưu trữ (nóng & lạnh)**, **Phát hiện bất thường**, **Phân tích nguyên nhân gốc rễ**, **Cảnh báo & Hành động**, **Phản hồi & Học liên tục**, và **Tri thức (knowledge base)**. Các lớp này tương ứng với các phase triển khai sẽ trình bày bên dưới.
*   **Cấu trúc repository & IaC:** Dự án sẽ được tổ chức theo cấu trúc thư mục rõ ràng, tách bạch theo module Terraform. Ví dụ, repository bao gồm các module: core (mạng, VPC giả lập), s3 (bucket lưu trữ), kinesis (stream ingest), lambda (hàm xử lý), sqs (hàng đợi), glue (ETL, catalog), stepfunctions (State Machine điều phối), eventbridge (sự kiện), opensearch (tìm kiếm & vector DB), knowledge-graph (đồ thị tri thức), rca-service (dịch vụ RCA, dùng LLM), alerting (cảnh báo), security (IAM, KMS), monitoring (CloudWatch hoặc tương đương). Việc đóng gói hạ tầng thành các module giúp dễ dàng quản lý, tái sử dụng và mở rộng. Tên tài nguyên, tags sẽ tuân theo chuẩn chung (bao gồm môi trường, tên ứng dụng, owner, cost-center, v.v.). Mọi cấu hình nhạy cảm (keys, secrets) sẽ dùng AWS Secrets Manager/Parameter Store khi lên AWS, đảm bảo bảo mật.
*   **Môi trường phát triển local vs AWS:** Để thuận tiện cho phát triển và thử nghiệm, hệ thống hỗ trợ hai chế độ chạy:
*   **Chế độ Local (POC):** Sử dụng LocalStack giả lập các dịch vụ AWS (S3, Kinesis, Lambda, v.v.). Những thành phần chưa hỗ trợ sẽ được thay thế bằng **Docker container** tương ứng (ví dụ: Redis container cho cache, OpenSearch container cho vector DB, Neo4j container cho graph DB, Spark container cho ETL...). Môi trường local cho phép chúng ta test toàn bộ pipeline mà không tốn chi phí cloud, đồng thời có thể chạy offline. Mã Terraform sẽ chứa các cấu hình endpoint tùy chọn để trỏ đến LocalStack khi is\_local = true. Ngoài ra, Docker Compose có thể được dùng để khởi động các dịch vụ phụ trợ (Redis, OpenSearch, Kafka...) phục vụ bản local.
*   **Chế độ AWS Thật:** Khi is\_local = false, Terraform sẽ trỏ tới các endpoint AWS thực. Lúc này, hệ thống sẽ sử dụng các dịch vụ AWS managed: ví dụ Kinesis Data Streams hoặc Amazon MSK thay cho Kinesis local, Amazon S3 thật thay cho S3 LocalStack, AWS Glue thật thay cho Spark local, Amazon Bedrock/SageMaker thay cho LLM container, Amazon ElastiCache thay cho Redis container, Amazon Neptune hoặc dịch vụ đồ thị thay cho Neo4j, v.v. Nhờ cấu trúc module và biến cấu hình, việc chuyển đổi này sẽ hạn chế tối đa thay đổi code. Tuy nhiên, cần chú ý thiết lập thêm VPC, subnet, bảo mật mạng khi lên AWS thật (ví dụ: chạy Lambda/SageMaker trong VPC, cấu hình Security Group, NAT Gateway cho private subnets, v.v.).
*   **Dữ liệu nguồn và mô phỏng dịch vụ:** Hệ thống hướng đến phân tích log/metric từ các ứng dụng microservice. Để **mô phỏng một kịch bản thực tế**, ta sẽ giả lập một số dịch vụ ứng dụng đơn giản (ví dụ: service _Đặt hàng_, service _Thanh toán_, _Định danh người dùng_, v.v.). Các service giả lập này sẽ định kỳ gửi logs và metrics (như CPU, memory, độ trễ, lỗi...) vào hệ thống thông qua các kênh ingest. Trong môi trường local, có thể triển khai các **Lambda producer** hoặc container script đóng vai trò generator, sinh sự kiện và đẩy vào Kinesis Streams tương ứng. Khi lên AWS thật, các sự kiện này có thể đến từ CloudWatch Logs/Metrics của các ứng dụng thực hoặc từ các agent thu thập metric (ví dụ: CloudWatch Agent, OpenTelemetry Collector) đẩy vào Kinesis Firehose.
*   **Sơ đồ luồng dữ liệu tổng quan:** Dưới đây là mô tả ngắn gọn luồng dữ liệu và xử lý trong hệ thống:
*   **Ingestion (Tiếp nhận dữ liệu):** Logs và metrics từ các service sẽ được đưa vào hệ thống qua các kênh streaming như **Amazon Kinesis** (hoặc Kafka). Dữ liệu thô cũng được lưu vào **Amazon S3 (raw bucket)** để đảm bảo khả năng lưu trữ lâu dài và làm nguồn cho xử lý batch.
*   **ETL & Data Lake:** Dữ liệu thô trên S3 được làm sạch và chuẩn hoá theo schema chung (ví dụ chuẩn thời gian, định danh service, đơn vị đo lường...). Quá trình ETL chạy theo lịch (hàng giờ hoặc hàng ngày) sử dụng **AWS Glue** (hoặc Spark job trong local), kết quả được ghi vào S3 (bucket **transformed/clean**). **Glue Data Catalog** được cập nhật để phục vụ truy vấn sau này (Athena/Redshift Spectrum).
*   **Storage (Nóng & Lạnh):** Dữ liệu sau xử lý được lưu ở hai nơi: **Storage lạnh** trên data lake S3 (đầy đủ lịch sử, dùng cho phân tích chuyên sâu và mô hình ML) và **storage nóng** sử dụng **Redis (ElastiCache)** hoặc cơ sở dữ liệu time-series (như Amazon Timestream) để truy vấn nhanh các metric gần thời gian thực. Storage nóng được cập nhật liên tục từ dòng sự kiện, cho phép hệ thống phát hiện bất thường trong vòng vài giây từ khi dữ liệu được gửi.
*   **Detection Engine (Phát hiện bất thường):** Nhiều phương pháp phát hiện bất thường được triển khai song song: phương pháp thống kê (như Seasonal Decomposition STL, IQR, Z-score), phương pháp ML (ví dụ Random Cut Forest - RCF, SR-CNN để phát hiện chuỗi bất thường) và phương pháp rule-based (dựa trên ngưỡng tĩnh hoặc thay đổi đột ngột). Các công việc này chạy dưới dạng **AWS Lambda** (hoặc container function local), kích hoạt theo lịch hoặc theo luồng sự kiện. Kết quả từ các phương pháp sẽ được tổng hợp tại **Decision Engine** (ví dụ dùng AWS Step Functions hoặc một Lambda điều phối) để bỏ phiếu, kết hợp tín hiệu và xác định **bất thường xác nhận** (anomaly confirmed) với độ tin cậy (confidence score) nhất định. Chỉ khi ít nhất 2 phương pháp đồng thuận hoặc điểm độ tin cậy vượt ngưỡng, sự kiện mới được coi là bất thường thực sự.
*   **Service Dependency & Topology:** Khi một bất thường được xác nhận, hệ thống tra cứu **topology** của toàn bộ ứng dụng để hiểu mức độ ảnh hưởng. Topology này mô tả quan hệ phụ thuộc giữa các service (gọi lên dịch vụ nào, phụ thuộc vào database nào...). Trên AWS, thông tin này có thể thu thập qua **AWS X-Ray**, **AWS App Mesh** hoặc dịch vụ khám phá service. Trong môi trường local, ta có thể quản lý một đồ thị phụ thuộc tĩnh dưới dạng file cấu hình hoặc cơ sở dữ liệu **Neo4j**. Topology giúp xác định **vùng ảnh hưởng (blast radius)**: ví dụ, nếu service A gặp lỗi, những service upstream/downstream nào sẽ bị tác động? Thông tin này sẽ được dùng để ưu tiên cảnh báo và phân tích nguyên nhân.
*   **Root Cause Analysis (Phân tích nguyên nhân gốc rễ):** Đây là lớp AI **đặc trưng** của hệ thống, sử dụng mô hình ngôn ngữ lớn và cơ sở tri thức. Khi có sự kiện bất thường, một dịch vụ RCA sẽ tổng hợp các thông tin liên quan: số liệu metric bất thường, log đoạn trích nổi bật, sự kiện triển khai (deploy) gần đó, tình trạng các service liên quan trong topology, và tri thức lịch sử (các sự cố tương tự, runbook). Dịch vụ RCA (local có thể là một container chạy mô hình LLM mở, trên AWS dùng **Amazon Bedrock** với model như Claude hoặc Titan) sẽ gọi **Vector Database** (như Amazon OpenSearch Serverless hoặc Pinecone) để tìm kiếm các tài liệu liên quan (runbook, hướng dẫn khắc phục) dựa trên embedding, sau đó phân tích và đưa ra **giả thuyết nguyên nhân** kèm độ tin cậy và đề xuất cách khắc phục. Kết quả này được lưu lại (S3) và gắn kèm trong cảnh báo gửi đi.
*   **Action & Alerting (Hành động & Cảnh báo):** Hệ thống gửi cảnh báo sự cố đến các kênh thích hợp: ví dụ, sự cố nghiêm trọng sẽ gửi **tin nhắn Slack** cho đội vận hành với nút _Acknowledge/Resolve_, tạo **sự kiện PagerDuty**, mở **ticket Jira**, hoặc email. Trước khi gửi, **Alert Manager** (một Lambda hoặc service) sẽ thực hiện **enrich** nội dung cảnh báo bằng thông tin từ RCA (nguyên nhân, gợi ý remediation, link đến tài liệu runbook) và sắp xếp mức độ ưu tiên. Để tránh trường hợp _"bão cảnh báo"_, hệ thống sử dụng SQS làm hàng đợi đệm, gom nhóm cảnh báo, gắn nhãn độ ưu tiên, và có cơ chế throttle (giới hạn tốc độ gửi) hoặc chuyển một số cảnh báo vào **Dead Letter Queue (DLQ)** nếu gửi thất bại nhiều lần.
*   **Feedback Loop (Phản hồi & Học liên tục):** Mỗi cảnh báo sau khi gửi đi sẽ được theo dõi phản hồi. Kỹ sư vận hành có thể đánh dấu trên giao diện (hoặc phản hồi qua Slack/Jira) xem cảnh báo đó là _False Positive_ hay _True Incident_, nguyên nhân thực sự ra sao, hành động khắc phục nào hiệu quả. Thông tin **feedback** này được hệ thống thu thập (lưu vào S3 hoặc database) để định kỳ huấn luyện lại mô hình phát hiện bất thường và hiệu chỉnh các tham số (threshold, trọng số voting). Một pipeline huấn luyện (ví dụ sử dụng **AWS SageMaker** cho mô hình ML hoặc job Spark cho rule mining) sẽ chạy trong Phase sau, giúp hệ thống ngày càng chính xác và giảm thiểu báo động giả. Bên cạnh đó, feedback về độ chính xác của phân tích RCA cũng được dùng để cải thiện bộ tri thức (nếu RCA đề xuất sai nguyên nhân, các kỹ sư có thể cập nhật lại runbook/hướng dẫn).
*   **Knowledge Base & Batch Processing:** Hệ thống tích hợp với các nguồn tri thức như **Confluence** (hoặc Wiki nội bộ) nơi lưu trữ thiết kế hệ thống, hướng dẫn vận hành, post-mortem các sự cố trước đây. Một thành phần crawler sẽ chạy theo lịch (ví dụ daily) để **thu thập tài liệu**, trích xuất nội dung chính, tạo **vector embeddings** và lưu vào **Vector DB** phục vụ bước RCA. Ngoài ra, hệ thống duy trì một **Knowledge Graph (đồ thị tri thức)** liên kết các thực thể như dịch vụ, thành phần hạ tầng, loại sự cố, người chịu trách nhiệm... Dữ liệu graph này (ví dụ trong **Amazon Neptune** hoặc OpenSearch nếu hỗ trợ) giúp trả lời các truy vấn như "ai là chuyên gia của service X", "những sự cố tương tự đã từng xảy ra với service Y chưa?" – hỗ trợ đắc lực cho RCA.
*   **Best Practices 2025:** Kiến trúc trên tận dụng các thông lệ hiện đại: kiến trúc **serverless** và container hoá để dễ mở rộng, kiến trúc **sự kiện điều khiển** để rời rạc hoá các thành phần (decoupling), kết hợp **AI (LLM)** nâng cao khả năng phân tích nguyên nhân, dùng **IaC** để quản lý môi trường hạ tầng thống nhất, tích hợp chặt chẽ **quan trắc/giám sát** (observability) và **bảo mật** ngay từ đầu (mã hoá dữ liệu S3, IAM phân quyền chặt chẽ, CloudTrail audit). Việc thiết kế từ đầu cho phép chạy môi trường local gần giống AWS (nhờ LocalStack) đảm bảo quá trình phát triển và thử nghiệm liên tục (CI/CD) nhanh chóng, giảm thiểu lỗi khi triển khai thật.

Sau đây, tài liệu sẽ trình bày chi tiết các **phase triển khai** từ Phase 0 đến Phase 9, tương ứng với các lớp kiến trúc đã nêu, kèm theo các bước cụ thể, tiêu chí hoàn thành và ước tính thời gian cho từng phase.

## Các Phase Triển khai và Tasks Chi tiết

Dự án được chia thành các phase (0 đến 9) tương ứng với các bước phát triển tuần tự. Mỗi phase liệt kê mục tiêu, các thành phần chính liên quan (dịch vụ AWS và bản local tương ứng), danh sách công việc cần thực hiện, các phụ thuộc, tiêu chí hoàn thành, và ước tính thời gian. Các phase được thiết kế tuần tự nhưng có thể thực hiện chồng lấn một phần để tối ưu tiến độ (ví dụ một số chuẩn bị nền tảng có thể làm song song).

### Phase 0: Nền tảng (Cấu trúc Repo, Scaffolding IaC, Môi trường Local)

*   **Mục tiêu:** Thiết lập nền tảng ban đầu cho dự án, bao gồm tổ chức repository, module Terraform, chuẩn hóa cấu hình và môi trường giả lập. Đảm bảo có thể dễ dàng chuyển đổi giữa chế độ local và AWS thật thông qua cấu hình, và các thành phần cơ bản của môi trường local (LocalStack, các container bổ trợ) đã sẵn sàng.
*   **Thành phần AWS (dự kiến):** Chưa có dịch vụ AWS cụ thể nào được tạo (chỉ cấu trúc IaC và config).
*   **Phiên bản Local:** Sử dụng **Terraform** với provider AWS trỏ tới LocalStack (qua endpoint\_override). Nếu dùng remote state cho Terraform POC, có thể tận dụng Terraform Cloud; nếu không, dùng local state tạm thời. Khởi động môi trường LocalStack và các container bổ sung (Redis, OpenSearch, Neo4j, v.v. trong Docker) để sẵn sàng cho các phase sau.
*   **Các bước triển khai chính (Tasks):**
*   **Tổ chức repository theo modules:** Thiết kế cấu trúc thư mục cho mã Terraform, chia thành các module độc lập (như đã liệt kê ở phần kiến trúc: core, s3, kinesis, lambda, glue, stepfunctions, eventbridge, sqs, opensearch, rca-service, alerting, feedback, knowledge, security, monitoring, v.v.). Tạo khung (scaffolding) cho từng module với file Terraform cơ bản (đầu ra/đầu vào, resource placeholder).
*   **Định nghĩa naming convention và tagging:** Thiết lập quy tắc đặt tên tài nguyên chung (ví dụ: tất cả resource bắt đầu với prefix <project>-<env>-...) và bộ thẻ tag mặc định (ví dụ: Environment, Application, Owner, CostCenter để phục vụ quản lý sau này).
*   **Cấu hình provider cho Local/AWS:** Thêm biến cấu hình is\_local (true/false) và các provider alias nếu cần. Khi is\_local=true, cấu hình AWS provider sẽ bao gồm endpoint trỏ tới LocalStack và region giả lập (ví dụ us-east-1), ngược lại khi false thì dùng AWS thật. Đảm bảo có thể chuyển đổi qua lại bằng cách đổi biến và chạy terraform init lại nếu cần.
*   **Thiết lập Terraform backend:** Cho POC local, có thể dùng backend cục bộ hoặc Terraform Cloud (remote state), miễn sao nhiều người có thể cộng tác. Chuẩn bị backend state cho môi trường AWS (S3 bucket + DynamoDB table để khóa state) để dùng ở phase sau.
*   **Thiết lập CI cơ bản cho Terraform:** Cài đặt các bước CI (ví dụ GitHub Actions) chạy terraform fmt và terraform validate với mỗi pull request để đảm bảo code Terraform luôn đúng định dạng và hợp lệ. (Nếu có thể, thiết lập thêm terraform plan tự động để review thay đổi).
*   **Chuẩn bị môi trường LocalStack + Docker Compose:** Cấu hình file docker-compose hoặc script để khởi chạy LocalStack container cùng các container khác (Redis cho ElastiCache, OpenSearch cho search và vector DB, Neo4j cho graph, Spark or Hive Metastore cho Glue, Grafana để mô phỏng CloudWatch dashboard, Kafka/Redpanda nếu cần). Đảm bảo các container này có thể giao tiếp với nhau (ví dụ: cùng network).
*   **Tài liệu và script khởi động:** Viết hướng dẫn ngắn (trong README) về cách khởi chạy môi trường local: bao gồm cài đặt LocalStack, chạy docker-compose lên các dịch vụ phụ trợ, cách export các endpoint (LocalStack cung cấp) để Terraform kết nối.
*   **Phụ thuộc:** Không có (đây là bước đầu tiên).
*   **Tiêu chí hoàn thành:**
*   Cấu trúc repo được khởi tạo đầy đủ, chạy terraform init và terraform validate không lỗi. Có thể chuyển qua lại biến is\_local và region mà không lỗi cấu hình.
*   LocalStack khởi động thành công, các container bổ trợ (Redis, OpenSearch, Neo4j, v.v.) sẵn sàng (kiểm tra bằng cách truy cập thử cổng dịch vụ hoặc log container không báo lỗi).
*   **Thời gian dự kiến:** 0.5 – 1 ngày (4–8 giờ).

### Phase 1: Data Sources & Ingestion Layer (Tiếp nhận dữ liệu thời gian thực)

*   **Mục tiêu:** Thiết lập kênh tiếp nhận dữ liệu realtime cho hệ thống. Các log và metric giả lập sẽ được đẩy vào hệ thống thông qua stream (Kinesis hoặc Kafka), đồng thời lưu trữ bản dữ liệu thô vào S3. Phase này xây dựng nền tảng cho các dữ liệu đầu vào của pipeline, đảm bảo dòng sự kiện realtime hoạt động ổn định.
*   **Thành phần AWS:** Amazon **Kinesis Data Streams** (hoặc Amazon MSK - Managed Kafka nếu cần), **Amazon S3** (các bucket raw), tùy chọn **CloudWatch Logs/Metrics** (trong kịch bản AWS, CloudWatch có thể là nguồn phát logs thực). Ngoài ra, có thể dùng **Kinesis Firehose** để đẩy dữ liệu từ stream vào S3 tự động.
*   **Phiên bản Local:** Sử dụng **Kinesis** của LocalStack để tạo các stream cho logs, metrics, APM (Application Performance Monitoring). Thay vì CloudWatch thật, sẽ có một **Lambda hoặc container generator** đóng vai trò sinh log/metric giả lập (ví dụ, một Lambda chạy mỗi 1 giây tạo sự kiện CPU, memory random cho một service). Nếu cần mô phỏng Kafka, có thể chạy một container Kafka (vd. bằng Redpanda) nhưng để đơn giản ban đầu, có thể chỉ dùng Kinesis.
*   **Các bước triển khai chính (Tasks):**
*   **Tạo S3 bucket cho dữ liệu raw:** Dùng Terraform module S3 để tạo các bucket lưu trữ dữ liệu thô, ví dụ: raw-logs, raw-metrics, raw-apm. Bật versioning và mã hóa SSE-KMS (trên AWS thật), thiết lập lifecycle rule (ví dụ tự động chuyển dữ liệu cũ sang Glacier sau X ngày ở môi trường thật, với local thì mô phỏng).
*   **Tạo Kinesis Streams:** Khai báo 3 Kinesis stream tương ứng cho luồng logs, metrics và APM. Với local, dùng LocalStack Kinesis (có thể giới hạn 1 shard mỗi stream cho đơn giản). Gán tên stream có prefix rõ ràng (vd: <project>-<env>-logs-stream).
*   **Triển khai Lambda producer (data generator):** Viết một function (có thể bằng Python) giả lập luồng sự kiện từ dịch vụ. Lambda này định kỳ (vd mỗi 1s) tạo một JSON message chứa thông tin log hoặc metric (ví dụ: {"service": "OrderService", "metric": "CPUUtilization", "value": 75, "timestamp": ...}) rồi đẩy vào Kinesis stream tương ứng. Tạo nhiều loại sự kiện khác nhau để mô phỏng cả logs (vd log lỗi, log cảnh báo) và metrics (CPU, memory, throughput).
*   **Kết nối Kinesis → S3 (persist stream):** Ở môi trường AWS, cấu hình **Kinesis Data Firehose** để tự động đọc từ stream và ghi dữ liệu ra S3 (theo định dạng và partition thời gian). Ở local do Firehose chưa có, có thể viết một **Lambda consumer** gắn với Kinesis stream (dùng chức năng Lambda trigger cho Kinesis) để nhận batch sự kiện, rồi ghi chúng vào S3 bucket raw dưới dạng file (chuẩn JSON Lines hoặc Parquet) theo partition (vd. raw-logs/2025/10/29/HH/...).
*   **Định nghĩa schema tạm thời cho dữ liệu:** Xác định cấu trúc JSON cho logs/metrics (các trường bắt buộc như timestamp, service\_name, metric\_name, value, etc.). Schema này sẽ được dùng trong phase ETL sau.
*   **Kiểm thử luồng ingest:** Chạy thử Lambda generator để bơm dữ liệu vào Kinesis. Xác nhận rằng dữ liệu được nhận và lưu vào S3 đúng như mong đợi. Ở local có thể dùng giao diện LocalStack hoặc AWS CLI giả lập để liệt kê các object trong S3 bucket raw sau khi generator chạy vài phút.
*   **Phụ thuộc:** Hoàn thành Phase 0 (các bucket, stream có thể tạo bằng Terraform sau khi scaffolding xong).
*   **Tiêu chí hoàn thành:**
*   Dữ liệu giả lập từ các "service" mẫu chảy vào Kinesis thành công và cuối cùng được lưu vào S3 **raw** theo đúng phân vùng thời gian đã định (ví dụ: có folder theo ngày/giờ, bên trong là file log).
*   Hệ thống ingest đạt độ trễ thấp: từ lúc đẩy vào Kinesis đến lúc file xuất hiện trên S3 chỉ vài giây (trong môi trường local demo có thể chấp nhận vài giây do Lambda poll).
*   Tốc độ ingest trong demo local có thể đạt vài nghìn sự kiện mỗi giây (tuỳ thuộc cấu hình máy), đủ để chứng minh khả năng mở rộng khi lên AWS.
*   **Thời gian dự kiến:** 2 – 3 ngày.

### Phase 2: ETL & Xử lý Batch (Làm sạch và Chuẩn hóa dữ liệu)

*   **Mục tiêu:** Xây dựng pipeline ETL (Extract-Transform-Load) để xử lý dữ liệu thô từ S3, chuẩn hoá về schema chung và lưu trữ vào khu vực lưu trữ đã qua xử lý (S3 transformed). Đồng thời, tạo lập **Data Catalog** giúp truy vấn dữ liệu thuận tiện. Kết quả của phase này là một **bộ dữ liệu sạch, thống nhất**, sẵn sàng cho các bước phân tích và phát hiện.
*   **Thành phần AWS:** AWS **Glue Crawlers** (tự động phát hiện schema), **Glue ETL Jobs** (Spark jobs) để xử lý dữ liệu, **Glue Data Catalog** để lưu metadata schema. Kết quả ETL ghi vào **Amazon S3** (bucket dữ liệu đã transform).
*   **Phiên bản Local:** LocalStack hỗ trợ Glue một phần hạn chế. Do đó, ở môi trường local sẽ dùng cách tiếp cận khác: có thể triển khai một container **Apache Spark** (hoặc dùng AWS Glue thật trên tài khoản dev nếu chấp nhận) để chạy job ETL. **Glue Data Catalog** có thể mô phỏng bằng **Hive Metastore** hoặc đơn giản hơn là lưu schema dưới dạng file JSON. Nếu khó giả lập hoàn toàn, có thể _bỏ qua bước crawler catalog trong bản local_ và chỉ tập trung vào việc transform dữ liệu.
*   **Các bước triển khai chính (Tasks):**
*   **Định nghĩa schema unified:** Thiết kế cấu trúc dữ liệu chung cho các bản ghi log/metric sau khi làm sạch. Ví dụ: một bản ghi metric thống nhất có các cột: timestamp (UTC), service\_id/tên service, metric\_name, value, unit, v.v. Logs có thể tách riêng schema (hoặc lưu chung với trường type để phân biệt). Xác định cách xử lý múi giờ, định dạng thời gian, đơn vị đo lường để mọi nguồn dữ liệu trở nên đồng nhất.
*   **Tạo job ETL (Spark/Glue):** Viết mã ETL (PySpark hoặc Scala) để đọc dữ liệu từ S3 raw (sử dụng wildcards theo partition), thực hiện các bước: lọc bỏ bản ghi lỗi, chuyển đổi đơn vị nếu cần (vd memory MiB -> MB), thêm cột chuẩn (vd environment, service group nếu có mapping), và ghi kết quả ra S3 **transformed** theo partition thích hợp (ví dụ partition theo date=YYYY-MM-DD và service=<name>). Trong Terraform, khai báo một **Glue Job** (loại Python Shell hoặc Spark ETL) trỏ tới script này.
*   **Thiết lập Glue Crawler (hoặc thủ công catalog):** Trên AWS, tạo Glue Crawler để quét S3 transformed và sinh database + table schema trong Glue Data Catalog. Đặt crawler chạy theo lịch (mỗi ngày hoặc mỗi khi có file mới). Trong local, nếu Glue không khả dụng, có thể viết script để ghi metadata schema (tên cột, kiểu dữ liệu) ra một file (coi như catalog tạm).
*   **Lập lịch batch ETL:** Sử dụng **EventBridge** (CloudWatch Events) để lên lịch kích hoạt job ETL. Ví dụ, mỗi giờ chạy job ETL một lần để xử lý dữ liệu mới trong giờ đó, hoặc mỗi ngày vào ban đêm tổng hợp lại. Ở local, EventBridge của LocalStack có thể dùng (nếu ổn định), hoặc có thể kích hoạt thủ công khi demo.
*   **Kiểm tra kết quả ETL:** Sau khi chạy ETL, kiểm tra S3 bucket _transformed_ có dữ liệu đầu ra theo cấu trúc đã định. Mở một vài file (CSV/Parquet) để xác nhận dữ liệu đã được chuyển đổi chính xác (đúng timezone, format). Trên AWS thật, thử truy vấn bằng **Athena** trên Data Catalog xem có ra kết quả.
*   **Phụ thuộc:** Phase 1 (có dữ liệu raw trong S3).
*   **Tiêu chí hoàn thành:**
*   Dữ liệu đã qua xử lý xuất hiện trong S3 bucket _transformed_, được phân vùng rõ ràng và tuân thủ schema thống nhất.
*   (Trên AWS) Glue Data Catalog có cơ sở dữ liệu và bảng cho dữ liệu log/metrics, schema chính xác, có thể query bằng Athena. (Trên local, có bản mô phỏng schema thành công).
*   Quá trình ETL hoạt động tự động theo lịch: khi đến lịch (hoặc khi có dữ liệu mới), job được kích hoạt và hoàn thành, không lỗi.
*   **Thời gian dự kiến:** 2 – 3 ngày.

### Phase 3: Lưu trữ Nóng & Lạnh (Storage Layer)

*   **Mục tiêu:** Thiết kế kiến trúc lưu trữ hai tầng: **lưu trữ nóng (Hot storage)** phục vụ truy vấn thời gian thực và **lưu trữ lạnh (Cold storage)** phục vụ lưu trữ dài hạn và truy vấn phân tích. Đảm bảo dữ liệu gần thời gian thực luôn sẵn sàng trong bộ nhớ nhanh (Redis hoặc CSDL time-series) để các thuật toán phát hiện có thể đọc nhanh, trong khi dữ liệu lịch sử vẫn an toàn trên S3 và có thể phân tích qua Athena/Redshift.
*   **Thành phần AWS:** Dịch vụ **Amazon ElastiCache (Redis)** cho cache nóng, **Amazon Timestream** (hoặc **Amazon DynamoDB** với schema time-series) cho lưu trữ time-series chuyên dụng (nếu sử dụng), **Amazon S3** (data lake lưu trữ lạnh), **Amazon Athena** (truy vấn S3 bằng SQL) hoặc **Redshift Spectrum**.
*   **Phiên bản Local:** Sử dụng container **Redis** (có thể cài module RedisTimeSeries nếu cần). Timestream không có bản local, có thể bỏ qua hoặc thay bằng việc sử dụng Redis/disk để lưu tạm. Athena cũng không có local; có thể mô phỏng bằng **Trino/Presto** container nếu muốn (không bắt buộc, có thể chỉ kiểm thử trên AWS).
*   **Các bước triển khai chính (Tasks):**
*   **Triển khai Redis Cache:** Tạo một **Redis container** trong docker-compose (phase 0 đã chuẩn bị). Trong Terraform, có module cho ElastiCache (khi lên AWS sẽ tạo cluster Redis). Xác định key schema cho Redis – ví dụ: sử dụng key dạng metrics:{service}:{metric\_name} trỏ đến một cấu trúc dữ liệu (list/SortedSet) chứa các điểm dữ liệu gần đây. Thiết lập TTL (thời gian sống) cho dữ liệu trong Redis, ví dụ giữ 24 giờ gần nhất.
*   **Cập nhật dữ liệu nóng realtime:** Xây dựng cơ chế đưa dữ liệu từ stream vào Redis gần như tức thì. Có thể tận dụng **Lambda consumer** (tương tự Lambda ở phase 1 ghi S3) để mỗi khi có event mới, ngoài lưu S3 cũng ghi luôn vào Redis. Đảm bảo việc ghi Redis tối ưu (có thể ghi theo batch mỗi vài giây thay vì từng record để giảm overhead).
*   **Cấu hình S3 lifecycle cho cold data:** Xác định chiến lược lưu trữ lạnh: dữ liệu trong S3 có thể sau X ngày chuyển sang Glacier hoặc xóa sau Y năm. Triển khai rule lifecycle trong Terraform cho các bucket raw và transformed (chỉ thực thi trên AWS, local thì mô phỏng logic).
*   **Chuẩn bị Athena/SQL query:** (Trên AWS) tạo sẵn một vài **Athena query** hoặc bảng bên Redshift Spectrum để chứng minh có thể truy cập dữ liệu cold. (Local có thể bỏ qua bước này, hoặc cài Trino để minh họa).
*   **Kiểm thử:** Đẩy một số dữ liệu qua toàn pipeline (đến sau Phase 2), sau đó truy vấn Redis xem có chứa các điểm dữ liệu mới nhất. Kiểm tra tốc độ đọc: truy vấn vài nghìn điểm gần nhất trong Redis xem mất bao lâu (< vài chục ms trong local). Đồng thời, thử query Athena trên S3 xem trả kết quả đúng.
*   **Phụ thuộc:** Hoàn thành Phase 1 (ingest) và Phase 2 (đã có dữ liệu transform để làm cold storage).
*   **Tiêu chí hoàn thành:**
*   **Redis cache** nhận được các metric mới trong vòng < 1–2 giây từ khi log/metric được gửi (đáp ứng yêu cầu real-time cho giai đoạn POC).
*   Dữ liệu **cold** đã lưu trên S3 đầy đủ, có cơ chế quản lý vòng đời rõ ràng. Truy vấn thử bằng Athena/Presto đọc được dữ liệu lịch sử.
*   Cấu hình hạ tầng cho Redis (hoặc Timestream) sẵn sàng để khi lên AWS có thể mở rộng (multi-AZ cluster cho Redis, hoặc bảng Timestream phân chia theo thời gian).
*   **Thời gian dự kiến:** 2 ngày.

### Phase 4: Detection Engine & Decision Engine (Máy phát hiện bất thường và quyết định)

*   **Mục tiêu:** Phát triển **bộ máy phát hiện bất thường** đa phương pháp, kết hợp cả thống kê, rule-based và AI/ML, sau đó tích hợp kết quả qua **Decision Engine** để xác định sự kiện bất thường một cách chính xác. Mục tiêu là giảm thiểu cảnh báo giả (_false positives_) bằng cách yêu cầu nhiều phương pháp đồng thuận hoặc trọng số cao, đồng thời phản ứng nhanh với bất thường thực (MTTD – Mean Time To Detect thấp).
*   **Thành phần AWS:**
*   **AWS Lambda** cho các thuật toán nhẹ (ví dụ: phân tích thống kê STL, IQR, Z-score trên cửa sổ dữ liệu ngắn; rule-based threshold).
*   **AWS SageMaker** cho mô hình ML nặng (triển khai model Random Cut Forest – RCF, hoặc LSTM/SR-CNN trên endpoint để real-time inference).
*   **AWS Step Functions** để điều phối workflow phát hiện & quyết định (chạy song song nhiều Lambda/Endpoint rồi tổng hợp kết quả).
*   **Amazon DynamoDB** hoặc S3 để tạm lưu kết quả bất thường trung gian.
*   **Amazon EventBridge** để trigger các chuỗi phát hiện (có thể dựa trên schedule mỗi phút hoặc event-driven khi có dữ liệu mới).
*   **Phiên bản Local:**
*   Tất cả các công việc phát hiện có thể chạy trong Lambda (LocalStack) hoặc container cục bộ. Mô hình ML có thể tải sẵn và infer ngay trong code (thay vì gọi endpoint) do khối lượng nhỏ trong demo.
*   SageMaker endpoint không có local, nên thay bằng cách đóng gói model (ví dụ mô hình RCF pre-trained) vào một Lambda container. Thư viện ML (như sagemaker-python-sdk hoặc scikit-learn, tensorflow) có thể được đưa vào container image.
*   Step Functions có hỗ trợ một phần trên LocalStack; nếu gặp khó, có thể dùng một Lambda làm coordinator thay thế cho State Machine (tức là Lambda này tự gọi các Lambda khác tuần tự/ song song rồi tổng hợp kết quả).
*   **Các bước triển khai chính (Tasks):**
*   **Định nghĩa input cho detection:** Xác định dạng đầu vào cho các thuật toán phát hiện. Thông thường, đầu vào là một đoạn chuỗi thời gian (time series) cho một metric nào đó thuộc một service, trong khoảng thời gian gần đây (vd 5 phút hoặc 1 giờ gần nhất). Cần quyết định **window size** (kích thước cửa sổ) và **sampling rate** (tần suất mẫu) cho phân tích. Chuẩn bị hàm lấy dữ liệu từ Redis (hot storage) tương ứng với window cần thiết.
*   **Triển khai Lambda cho phương pháp thống kê:** Viết các hàm Lambda thực hiện phát hiện bất thường bằng kỹ thuật thống kê cổ điển:
    *   **STL decomposition + IQR**: tách chuỗi thành trend/seasonal/residual rồi dùng IQR trên residual để tìm outlier.
    *   **Z-Score / EWMA**: tính z-score của điểm mới nhất dựa trên cửa sổ trung bình trượt và độ lệch chuẩn; phát hiện spike khi z vượt ngưỡng.
    *   Các Lambda này nhận input (chuỗi thời gian) và trả output gồm: có bất thường (true/false), độ tin cậy/tín hiệu (score), và lý do (ví dụ: "CPU tăng 3σ so với trung bình").
*   **Triển khai Lambda rule-based:** Định nghĩa một tập **rule** (quy tắc) dựa trên ngưỡng tĩnh hoặc điều kiện logic, ví dụ: "CPU > 90% trong 5 phút", "HTTP error rate > 5%". Các rule này có thể lưu trong DynamoDB (cấu hình) hoặc code cứng cho demo. Lambda rule-based sẽ kiểm tra dữ liệu hiện tại đối chiếu các rule, output bất thường nếu vi phạm.
*   **Tích hợp ML model cho anomaly detection:** Lựa chọn một mô hình ML/AI. Ví dụ:
    *   **Random Cut Forest (RCF):** mô hình unsupervised của Amazon để phát hiện điểm bất thường trong phân phối dữ liệu.
    *   **SR-CNN (Seasonal Hybrid ESD):** mô hình deep learning của Azure dùng trong Anomaly Detector.
    *   Do trong local không có SageMaker, ta có thể sử dụng một thư viện Python để chạy mô hình đã huấn luyện. Có thể offline huấn luyện RCF trên dataset mẫu rồi lưu model (hoặc dùng thư viện sklearn.ensemble.IsolationForest như một thay thế). Tích hợp model này vào Lambda (có thể cần container vì kích thước thư viện).
    *   Lambda ML sẽ nhận chuỗi dữ liệu, chạy model.predict và trả về kết quả (các điểm nào là anomaly hoặc score).
*   **Xây dựng Decision Engine:** Sử dụng **AWS Step Functions** để orchestration: Step Functions sẽ song song gọi các Lambda: stats, rule, ML cho mỗi metric, sau đó tổng hợp kết quả. Define logic:
    *   Nếu từ 2 trong 3 phương pháp báo hiệu bất thường, hoặc tổng hợp trọng số (ví dụ ML 40%, Stats 35%, Rule 25%) vượt ngưỡng 70%, thì kết luận **Anomaly Confirmed**.
    *   Nếu chỉ một phương pháp cảnh báo và mức độ yếu, có thể coi là nhiễu (Anomaly Rejected).
    *   Tính toán **confidence score** (độ tin cậy) cho anomaly dựa trên số phiếu và trọng số. Gán nhãn **mức độ nghiêm trọng (severity)** dựa trên biên độ lệch (nếu CPU tăng gấp đôi bình thường có thể severity cao hơn việc tăng 10%).
    *   Decision Engine sẽ tạo một bản ghi kết quả (gồm timestamp, service, metric, giá trị, phương pháp nào triggered, score, severity, etc.) và lưu vào S3 (folder anomalies/) hoặc DynamoDB. Đồng thời phát ra một sự kiện mới trên EventBridge kiểu anomaly.confirmed để kích hoạt các bước tiếp theo (RCA, alert).
*   **Xử lý nhóm (aggregation) và giảm nhiễu:** Nếu có nhiều anomaly cùng lúc (ví dụ một loạt metric cùng bất thường cho một service), Decision Engine có thể nhóm chúng thành một sự kiện (vd. "Service A gặp nhiều bất thường về CPU, Memory cùng lúc"). Thiết lập cơ chế gộp này để tránh gửi quá nhiều cảnh báo trùng lặp.
*   **Kiểm thử với dữ liệu bất thường giả:** Tạo một tình huống giả lập (vd. service OrderService CPU tăng từ 50% lên 95% đột ngột) xem các Lambda có phát hiện không. Điều chỉnh tham số ngưỡng/trọng số nếu cần để đạt được chỉ khi thật sự có sự kiện lớn mới trigger anomaly.confirmed.
*   **Phụ thuộc:** Phase 3 (có dữ liệu trong Redis để đọc), Phase 2 (có dữ liệu sạch để train model nếu cần).
*   **Tiêu chí hoàn thành:**
*   Hệ thống có thể phát hiện một bất thường giả lập và tạo record anomaly với độ trễ tổng cộng < 5 giây kể từ lúc dữ liệu bất thường xuất hiện.
*   Kết quả anomaly bao gồm thông tin tổng hợp từ nhiều phương pháp (ví dụ: "detected by Statistical & ML", confidence ~ 85%, severity: high).
*   Các thành phần Lambda/Step Functions hoạt động ổn định, log không báo lỗi. Trường hợp không có bất thường, hệ thống không gây quá nhiều nhiễu (tức là FP rate chấp nhận được, ví dụ <5% trong thử nghiệm).
*   **Thời gian dự kiến:** 4 – 6 ngày.

### Phase 5: Service Dependency & Topology (Đồ thị phụ thuộc dịch vụ)

*   **Mục tiêu:** Thu thập và quản lý thông tin **topology** của hệ thống microservices để hỗ trợ đánh giá ảnh hưởng khi xảy ra sự cố. Khi một service gặp lỗi hoặc bất thường, có thể nhanh chóng xác định các service liên quan (upstream/downstream) để đánh giá **blast radius** và tập trung xử lý. Phase này xây dựng hoặc mô phỏng một **đồ thị phụ thuộc (dependency graph)** của các service.
*   **Thành phần AWS:**
*   **AWS X-Ray** (thu thập trace và sơ đồ service map),
*   **AWS App Mesh** hoặc **Service Catalog/Registry** (nếu có, để định nghĩa topology ứng dụng),
*   **Amazon Neptune** (CSDL đồ thị) hoặc sử dụng tính năng graph của OpenSearch để lưu trữ mối quan hệ.
*   **AWS S3** (lưu file JSON topology, hình ảnh sơ đồ nếu cần).
*   **Phiên bản Local:**
*   Do X-Ray khó mô phỏng đầy đủ, ban đầu có thể dùng một file cấu hình YAML/JSON tĩnh liệt kê các service và quan hệ. Ví dụ: Service A gọi B và C; Service B gọi D; v.v.
*   Sử dụng **Neo4j** container làm nơi lưu trữ đồ thị phụ thuộc (có thể nhập file YAML vào Neo4j).
*   Visualization (trực quan hóa): trong local, có thể dùng một công cụ đồ thị (như Neo4j Browser hoặc Grafana plugin) hoặc đơn giản tạo một trang web tĩnh đọc file JSON vẽ sơ đồ.
*   **Các bước triển khai chính (Tasks):**
*   **Xác định định dạng đồ thị:** Thiết kế cách biểu diễn mỗi **node** (nút) trong đồ thị – thường tương ứng một service hoặc một thành phần (database, queue). **Edge** (cạnh) biểu diễn sự phụ thuộc hoặc gọi lẫn nhau giữa các nút. Có thể thêm thuộc tính cho edge như loại giao tiếp (HTTP, gRPC), tần suất gọi, v.v.
*   **Thu thập hoặc định nghĩa topology:** Nếu có sẵn dữ liệu từ X-Ray (trên AWS), thiết lập X-Ray Daemon và thu thập service map. Nếu chưa có, tạo thủ công file mô tả. Ví dụ YAML:
*   services:  
    \- name: OrderService  
    dependencies: \[ PaymentService, InventoryService \]  
    \- name: PaymentService  
    dependencies: \[ BillingAPI \]  
    ...
*   Lưu file này vào S3 hoặc đóng gói trong mã.
*   **Đưa dữ liệu vào Neo4j (local):** Dùng Neo4j Docker, tạo các node và relationships từ file trên. (Trên AWS thật, có thể bỏ qua bước này và dùng Neptune sau). Xác minh bằng câu lệnh Cypher đơn giản (MATCH (a)-\[:CALLS\]->(b)...).
*   **Cập nhật trạng thái service:** Viết một Lambda (hoặc một module trong code) để đánh dấu trạng thái của mỗi service (Healthy/Degraded/Critical) dựa trên dữ liệu bất thường. Cụ thể: khi nhận sự kiện anomaly.confirmed từ Phase 4, xác định service liên quan, cập nhật trạng thái của node đó trong đồ thị (ví dụ gắn thuộc tính status = "critical"). Đồng thời, lan truyền hoặc đánh dấu các service lân cận: upstream có thể "warning" do gián tiếp bị ảnh hưởng, downstream có thể "degraded" nếu chain bị chậm.
*   **Lưu trữ topology và hiển thị:** Lưu bản snapshot topology (có trạng thái) ra S3 dưới dạng file JSON hoặc hình ảnh (có thể dùng GraphViz vẽ nhanh). Chuẩn bị tích hợp hiển thị trên dashboard (có thể là một trang React nhỏ hoặc Grafana panel) để khi demo có thể mở xem **sơ đồ hệ thống** với highlight những phần đang sự cố (màu đỏ/vàng/xanh).
*   **Tính toán blast radius:** Triển khai một hàm phân tích đồ thị: khi một service A "Critical", tìm tất cả các service upstream và downstream trong K bước (có thể đặt K=2 hoặc 3) để xác định phạm vi ảnh hưởng. Ví dụ: PaymentService lỗi có thể ảnh hưởng tới OrderService (upstream gọi Payment) và BillingAPI (downstream bị Payment gọi). Thông tin này sẽ được đưa vào báo cáo RCA và cảnh báo.
*   **Phụ thuộc:** Phase 4 (có sự kiện anomaly xác nhận), Phase 1 (danh sách service từ log ingest).
*   **Tiêu chí hoàn thành:**
*   Khi xảy ra một anomaly, hệ thống xác định được **các service liên quan** trong đồ thị và gán trạng thái đúng (ví dụ: service gặp sự cố màu đỏ, các service phụ thuộc trực tiếp màu vàng).
*   Có thể trực quan xem **sơ đồ topology** và thấy rõ phần bị sự cố được highlight. Điều này chứng minh hệ thống nắm bắt được bối cảnh kiến trúc, giúp người vận hành nhanh chóng định vị vấn đề.
*   (Trên AWS thực) nếu tích hợp X-Ray, có thể thấy các service map tự động dựa trên trace.
*   **Thời gian dự kiến:** 2 – 3 ngày.

### Phase 6: Root Cause Analysis Engine (Động cơ phân tích nguyên nhân gốc rễ bằng AI & Tri thức)

*   **Mục tiêu:** Phát triển thành phần **Root Cause Analysis (RCA)** sử dụng AI (cụ thể là mô hình ngôn ngữ lớn - LLM) kết hợp với kho tri thức để tự động suy luận nguyên nhân gốc rễ của sự cố. Thành phần này sẽ **thu thập tất cả tín hiệu và ngữ cảnh** liên quan đến sự cố (bất thường từ Phase 4, trạng thái topology từ Phase 5, log chi tiết, lịch sử deploy, v.v.), sau đó sử dụng LLM để phân tích, đối chiếu với tri thức quá khứ (runbook, sự cố tương tự) và đưa ra kết luận về nguyên nhân khả dĩ cũng như đề xuất cách xử lý. Đây là bước nâng cao giá trị của hệ thống, giúp giảm thời gian phân tích sự cố (MTTR).
*   **Thành phần AWS:**
*   **Amazon Bedrock** (hoặc Amazon SageMaker Endpoint hosting một LLM như GPT-J, GPT-4...) để truy vấn mô hình ngôn ngữ lớn một cách bảo mật,
*   **Amazon S3** để lưu trữ các tài liệu tri thức (runbooks, post-mortems),
*   **Vector Database**: có thể dùng **Amazon OpenSearch Serverless** với plugin k-NN, hoặc dịch vụ vector DB chuyên dụng như **Pinecone**, để lưu embedding của tài liệu,
*   **AWS Lambda** hoặc **Step Functions** để điều phối quá trình RCA,
*   **Confluence API** (hoặc Jira, Github Wiki) để kéo thông tin từ hệ thống tài liệu nội bộ.
*   **Phiên bản Local:**
*   Thay vì Bedrock, sử dụng một dịch vụ RCA giả lập: có thể chạy một mô hình LLM open-source (như GPT-J-6B hoặc Llama 2) trong một container (tuy nhiên điều này nặng, nên có thể **mock** kết quả hoặc dùng API một mô hình nhỏ qua internet nếu được). Hoặc đơn giản hơn, viết một logic rule-based kết hợp tìm kiếm từ kho tri thức cục bộ để giả lập quá trình suy luận (phục vụ demo).
*   Vector DB local: dùng **OpenSearch** container đã có, bật tính năng k-NN để lưu vector embedding cho tài liệu. Hoặc dùng **Weaviate**/**FAISS** container.
*   Confluence: nếu có sandbox API, có thể gọi trực tiếp; nếu không, dùng file tài liệu tĩnh để mô phỏng.
*   **Các bước triển khai chính (Tasks):**
*   **Chuẩn hoá input cho RCA:** Thiết kế cấu trúc dữ liệu đầu vào mà RCA Engine sẽ nhận khi có anomaly. Gồm có:
    *   Thông tin bất thường: service nào, metric nào, giá trị, thời gian, độ nghiêm trọng.
    *   Ngữ cảnh hệ thống: các service liên quan (topology), sự kiện deploy (nếu trong khoảng 1h trước đó service này vừa deploy phiên bản mới, thông tin này rất hữu ích), tình trạng hạ tầng (có node nào down?, spike traffic?).
    *   Dữ liệu chi tiết: trích xuất 5–10 dòng log tiêu biểu quanh thời điểm xảy ra bất thường (nếu log level error, warning có trong raw logs).
    *   Thông tin tri thức: các keyword chính (service name, error code, metric name) để tra cứu tài liệu.  
        Gói tất cả vào một payload (có thể là JSON) truyền đến RCA service.
*   **Xây dựng kho tri thức & vector embeddings:** Thu thập trước một tập tài liệu dùng cho RCA:
    *   Runbook/hướng dẫn vận hành cho các dịch vụ (vd: "Nếu CPU tăng cao, kiểm tra A, B, C...").
    *   Các post-mortem, báo cáo sự cố cũ; FAQ và kinh nghiệm từ đội vận hành.
    *   Lưu các tài liệu này (có thể dưới dạng Markdown, PDF) vào một S3 bucket (knowledge-base/).
    *   Tạo một job (có thể là một script Python) để đọc từng tài liệu, dùng mô hình **SentenceTransformer** (một dạng embedding model) để chuyển từng đoạn văn thành vector. Lưu các vector này vào Vector DB (OpenSearch/Weaviate) cùng với metadata (tiêu đề tài liệu, link).
    *   Thiết lập API tìm kiếm semantic: cho phép gửi một truy vấn (là đoạn mô tả sự cố) và trả về những đoạn tài liệu tương tự nhất (dựa trên độ gần vector).
*   **Phát triển logic RCA (prompt + suy luận):** Xây dựng một chuỗi bước (có thể trong Step Functions hoặc code tuần tự):
    1.  **Contextualization:** Tiếp nhận input anomaly, chuẩn bị một đoạn prompt mô tả vấn đề bao gồm tất cả thông tin đã có (từ input payload ở trên).
    2.  **Retrieval:** Từ thông tin này, trích xuất các từ khóa chính (service, error, symptom) để truy vấn Vector DB. Lấy về top 3–5 đoạn tài liệu liên quan nhất.
    3.  **LLM Reasoning:** Gửi tới mô hình LLM (Bedrock hoặc local LLM) một prompt bao gồm: mô tả sự cố + các đoạn tri thức tìm được. Yêu cầu LLM phân tích: _Nguyên nhân gốc có thể là gì? Bằng chứng nào ủng hộ? Đề xuất bước khắc phục?_
    4.  **Synthesis:** Xử lý đầu ra từ LLM, định dạng lại thành cấu trúc cố định: ví dụ JSON gồm các trường root\_cause\_hypothesis, confidence, evidence, recommended\_actions, related\_docs. Định nghĩa cấu trúc này để dễ sử dụng ở bước sau.
    5.  **Output:** Lưu kết quả vào S3 (anomaly\_rca/ với key gồm incident id). Đồng thời, phát một sự kiện (EventBridge) hoặc gọi trực tiếp Alerting phase, thông báo rằng RCA result đã sẵn sàng cho sự cố X.
*   **Tích hợp với Decision Engine:** Đảm bảo rằng khi một anomaly.confirmed được tạo ở Phase 4, nó sẽ trigger quá trình RCA này. Cách tích hợp: có thể cấu hình EventBridge rule lắng nghe sự kiện anomaly.confirmed rồi khởi chạy một Lambda (RCA Orchestrator) thực hiện các bước trên.
*   **Kiểm thử RCA:** Mô phỏng một tình huống (ví dụ: _Service OrderService CPU tăng 95% sau khi deploy phiên bản mới, log có lỗi kết nối database_), xem RCA output đưa ra gì. Nếu dùng LLM thật (Bedrock), kiểm tra câu trả lời có hợp lý và gồm các phần yêu cầu không. Nếu dùng logic mock, kiểm tra output có dạng chuẩn. Hiệu chỉnh prompt, bộ tài liệu để cải thiện câu trả lời.
*   **Phụ thuộc:** Phase 4 (có anomaly), Phase 5 (có topology), Phase 9 (kho tri thức chuẩn bị ở phase 9 cũng liên quan trực tiếp). Tuy nhiên có thể bắt đầu xây dựng RCA song song với phase 9.
*   **Tiêu chí hoàn thành:**
*   Với một sự cố giả định (ví dụ CPU spike do loop vô tận trong code), hệ thống RCA đưa ra được **giả thuyết nguyên nhân** hợp lý (ví dụ: "Có thể do deploy phiên bản mới chứa bug gây leak CPU"), kèm theo các bằng chứng (log error, việc mới deploy) và đề xuất giải pháp (rollback, kiểm tra service X).
*   Kết quả RCA có cấu trúc rõ ràng, bao gồm chỉ ra tài liệu tham khảo (runbook nào liên quan, link đến Confluence).
*   Thời gian tạo báo cáo RCA nhanh (vài giây nếu dùng local LLM nhỏ, hoặc vài trăm mili giây nếu Bedrock). Nhìn chung, tổng thời gian từ lúc anomaly xác nhận đến khi RCA xong và gửi cảnh báo vẫn trong mức vài giây đến dưới 1 phút (chấp nhận được do RCA có thể phức tạp hơn).
*   **Thời gian dự kiến:** 3 – 5 ngày.

### Phase 7: Action & Alerting Layer (Thông báo & Hành động tự động)

*   **Mục tiêu:** Xây dựng lớp cảnh báo và hành động, điều phối việc gửi thông tin sự cố đến đúng kênh và người chịu trách nhiệm. Mỗi khi có sự cố (đã phân tích RCA), hệ thống sẽ **enrich** (bổ sung ngữ cảnh) cho cảnh báo, sau đó gửi tới các kênh như Slack, PagerDuty, email, hoặc tạo ticket Jira. Đồng thời, hệ thống cung cấp cơ chế để kỹ sư tương tác ngược (vd bấm _Acknowledge_ trên Slack để đánh dấu đã nhận). Mục tiêu là đảm bảo sự cố được thông báo kịp thời, đúng đối tượng, với thông tin đầy đủ nhưng tránh trùng lặp và quá tải.
*   **Thành phần AWS:**
*   **Amazon SQS** làm hàng đợi đệm cho sự kiện cảnh báo (có thể dùng các queue ưu tiên khác nhau, và 1 Dead Letter Queue để lưu những cảnh báo không gửi được),
*   **AWS Lambda** cho khâu **Alert Enrichment** (lấy thông tin RCA, runbook link, on-call person, v.v.),
*   **Amazon SNS** (hoặc AWS SES) cho gửi email,
*   Tích hợp **Slack API, PagerDuty API, Jira API** thông qua Lambda (sử dụng webhook hoặc SDK tương ứng),
*   **Amazon CloudWatch Dashboards** để hiển thị realtime tình trạng (hoặc thay bằng Grafana/ElasticHQ nếu không dùng CloudWatch).
*   **Phiên bản Local:**
*   Dùng **SQS** của LocalStack để mô phỏng hàng đợi.
*   Slack/PagerDuty/Jira có thể dùng tài khoản sandbox hoặc tạo request tới url dummy (kiểm tra log thay vì thật sự gửi). Slack có thể dùng webhook URL của workspace test. PagerDuty cung cấp API sandbox. Jira có thể có dự án thử.
*   CloudWatch Dashboard không có local, có thể thay bằng **Grafana** để vẽ bảng điều khiển realtime (nối tới dữ liệu Redis, S3).
*   **Các bước triển khai chính (Tasks):**
*   **Thiết kế Alert Manager & Routing:** Xác định các **luồng cảnh báo**: ví dụ, cảnh báo **Critical** cho dịch vụ quan trọng sẽ gửi PagerDuty (gọi điện nếu cần) + Slack kênh #alerts-critical; cảnh báo **Medium** chỉ gửi Slack và tạo Jira ticket cho nhóm xử lý sau; cảnh báo **Low** có thể chỉ log lại chứ không gửi. Xác định rule routing dựa trên: độ nghiêm trọng, loại sự cố, thời gian (giờ hành chính hay không), và team phụ trách (mapping dịch vụ → team/on-call).
    *   Tạo một bảng cấu hình (có thể trong DynamoDB hoặc file JSON) liệt kê các rule trên.
*   **Enrichment Lambda:** Viết Lambda lấy sự kiện anomaly.rca.ready (đã có RCA result) từ Phase 6. Lambda sẽ làm các việc:
    *   Tra cứu thông tin on-call của dịch vụ (có thể lưu trong 1 file config: ví dụ service A on-call: @user1).
    *   Lấy kết quả RCA từ S3 (hoặc từ payload sự kiện) bao gồm nguyên nhân và đề xuất.
    *   Lấy link runbook liên quan (có thể đã kèm trong RCA).
    *   Tạo message chi tiết: tiêu đề (ví dụ: "\[Critical\] OrderService CPU spike - Possible memory leak"), nội dung gồm mô tả sự cố, nguyên nhân giả định, đề xuất, ảnh snapshot (nếu có dashboard), link runbook, nút/nội dung cho acknowledge.
    *   Đẩy message này vào SQS queue tương ứng với mức độ (ví dụ: critical-queue, normal-queue).
*   **Workers gửi thông báo:** Triển khai các Lambda consumer cho hàng đợi SQS:
    *   Lambda đọc message cảnh báo từ queue.
    *   Dựa vào kênh đích (xác định từ nội dung hoặc queue), format payload: ví dụ, Slack message dùng JSON với blocks (nếu tương tác), PagerDuty dùng sự kiện API format, Jira dùng REST tạo issue.
    *   Gửi tới API tương ứng (sử dụng thư viện hoặc HTTP request).
    *   Xử lý phản hồi: nếu gửi thành công, log lại và kết thúc; nếu thất bại (ví dụ API limit), có thể push vào DLQ hoặc retry với backoff.
*   **Thiết lập tương tác từ kênh:** Với Slack, tạo một **Slack App** cho phép nhận tương tác (interactive components). Khi người dùng bấm _Acknowledge_ hoặc _Resolved_, Slack sẽ gọi một webhook (hoặc gửi message vào một endpoint). Thiết kế một **Webhook Lambda** để nhận các tương tác này: nếu _Acknowledge_, hệ thống có thể đánh dấu sự kiện trong database là đã nhận (và ngừng gửi lặp lại nếu có cơ chế nhắc lại); nếu _Resolve_, có thể tự động đóng ticket Jira hoặc gửi lệnh hủy PagerDuty. (Phần này có thể phức tạp, trong POC có thể chỉ log nhận được).
*   **Dashboard realtime:** Thiết lập một bảng dashboard giám sát chung cho đội vận hành:
    *   Trực quan các metric chính và đánh dấu tại thời điểm có anomaly (ví dụ vẽ biểu đồ CPU, có highlight khoảng đỏ khi sự cố xảy ra).
    *   Danh sách sự cố gần đây, trạng thái (ack/resolved).
    *   Ở local, làm đơn giản bằng Grafana: kết nối Grafana tới Redis (hoặc Prometheus if any) để lấy metrics, dùng annotation API để đánh dấu sự cố.
    *   Hoặc tạo một trang web tĩnh đọc từ S3 (S3 có thể chứa lịch sử sự cố) và hiển thị.
*   **Kiểm thử end-to-end:** Thực hiện một luồng hoàn chỉnh: từ ingest -> anomaly -> RCA -> alert:
    *   Xem Slack sandbox nhận được message đầy đủ nội dung, định dạng tốt (có thể dưới dạng block kit).
    *   Kiểm tra Jira sandbox có ticket được tạo (nếu tích hợp).
    *   Xem PagerDuty (nếu có) nhận alert và tạo incident.
    *   Thao tác thử nút _Acknowledge_ (nếu hiện thực) xem hệ thống nhận biết và log.
    *   Kiểm tra queue DLQ trống (nghĩa là không có lỗi gửi alert nào nghiêm trọng).
*   **Phụ thuộc:** Phase 6 (có kết quả RCA), Phase 4 (có anomaly trigger).
*   **Tiêu chí hoàn thành:**
*   Cảnh báo được gửi đến đúng kênh trong vòng < 5 giây sau khi RCA hoàn tất. Nội dung cảnh báo phong phú, có thông tin nguyên nhân và hướng xử lý, giúp người nhận **hiểu ngay vấn đề** mà không cần tra cứu nhiều.
*   Không xảy ra tình trạng gửi lặp hoặc gửi quá nhiều (nhờ cơ chế gộp/đệm SQS). Ví dụ, khi một service gặp 5 metric bất thường cùng lúc, hệ thống gửi một alert tổng hợp thay vì 5 cái riêng lẻ.
*   Người vận hành có phương tiện để phản hồi (ít nhất là acknowledge bằng tay, hoặc thông qua UI nếu có).
*   Dashboard phản ánh trạng thái hệ thống, có hiển thị sự cố theo thời gian thực.
*   **Thời gian dự kiến:** 2 – 3 ngày.

### Phase 8: Feedback Loop & Continuous Learning (Phản hồi và Học liên tục)

*   **Mục tiêu:** Đóng gói cơ chế **phản hồi liên tục** để cải thiện hệ thống theo thời gian. Sau mỗi sự cố, thông tin phản hồi từ người vận hành sẽ được thu thập: cảnh báo đó có đúng không, RCA có chính xác không, hành động đề xuất có hiệu quả không. Dữ liệu phản hồi này được sử dụng để **huấn luyện lại mô hình ML**, điều chỉnh ngưỡng của rule, trọng số voting, và cập nhật tri thức. Mục tiêu là giảm thiểu false positives, tăng độ chính xác của RCA, và tinh chỉnh hệ thống cho phù hợp với môi trường cụ thể.
*   **Thành phần AWS:**
*   **Amazon S3** để lưu trữ dữ liệu phản hồi và bộ dữ liệu training mới,
*   **AWS Glue** (hoặc Lambda) để định kỳ tổng hợp phản hồi thành dataset,
*   **AWS SageMaker** để huấn luyện lại mô hình ML (RCF, CNN...) hoặc tune hyperparameters,
*   **AWS Lambda** để cập nhật tham số (như cập nhật file cấu hình threshold, rule) và triển khai mô hình mới (CI/CD cho model),
*   **Amazon CloudWatch** để giám sát các chỉ số FP rate, detection delay trước và sau khi cập nhật.
*   **Phiên bản Local:**
*   Có thể xây dựng một trang web hoặc form đơn giản (ví dụ React hoặc một trang HTML tĩnh) cho phép nhập feedback (hoặc đọc từ Slack command). Feedback được ghi vào S3 (local) dưới dạng file JSON dòng hoặc CSV.
*   Dùng Spark (local) hoặc script Python để đọc tất cả feedback, tổng hợp thống kê (bao nhiêu cảnh báo đúng, bao nhiêu sai, lý do sai thường gặp...).
*   Mô phỏng training: chạy một job sklearn/PyTorch cục bộ trên dataset nhỏ – ví dụ train một Isolation Forest mới, hoặc điều chỉnh threshold cho z-score dựa trên tỷ lệ FP quan sát.
*   Cập nhật tham số: ghi các ngưỡng mới, trọng số voting mới vào S3 (hoặc DynamoDB local). Lần chạy detection tiếp theo sẽ dùng giá trị mới (có thể thiết kế để Lambda detection đọc cấu hình từ S3 mỗi khi chạy).
*   **Các bước triển khai chính (Tasks):**
*   **Định nghĩa schema feedback:** Xác định những gì cần thu thập sau sự cố. Ví dụ: incident\_id, is\_false\_positive (yes/no), root\_cause\_correct (yes/no), user\_comments, severity\_adjustment (none/up/down), remediation\_effective (yes/no). Những thông tin này giúp biết cảnh báo có đúng hay gây phiền hà, RCA đoán đúng chưa, mức độ nghiêm trọng có bị đánh giá sai không, cách khắc phục đề xuất có giải quyết được vấn đề không.
*   **Thu thập feedback:** Tạo một giao diện hoặc cách thức để người vận hành gửi feedback. Có thể đơn giản là gửi một tin nhắn Slack command như /feedback incident123 false RCA\_wrong "actual cause was config issue". Hoặc một form web liên kết với hệ thống SSO. Trong POC local, có thể tạo một trang web nhỏ liệt kê các sự cố vừa qua và có nút cho mỗi sự cố: "Đúng", "Sai", "RCA Đúng/Sai", kèm ô nhập nhận xét. Submit sẽ gọi API Gateway (LocalStack) đến Lambda để ghi nhận. (Hoặc đơn giản hơn: thu thập feedback offline cho demo).
*   **Lưu trữ feedback:** Triển khai một **Lambda API** (nếu dùng API Gateway) hoặc cơ chế nhận feedback, lưu các bản ghi feedback vào S3 (ví dụ file feedback/2025-10.csv chứa các phản hồi). Đồng thời, có thể lưu vào DynamoDB để tiện tra cứu nhanh.
*   **ETL feedback thành dataset:** Viết một job (Glue hoặc Spark) đọc tất cả feedback từ S3, làm sạch và tổng hợp thành bộ dữ liệu training. Ví dụ thêm cột label cho mỗi anomaly: FP hoặc TP. Kết hợp với dữ liệu raw (có thể cần join anomaly với metric pattern) để tạo feature nếu cần huấn luyện mô hình. Kết quả dataset này lưu ra S3 (folder training-dataset/).
*   **Retraining model & tuning:** Sử dụng SageMaker (trên AWS) để chạy lại việc huấn luyện mô hình ML dùng trong Phase 4 với dữ liệu mới: ví dụ huấn luyện Isolation Forest hoặc RCF trên dữ liệu metric có gán nhãn (nếu có). Hoặc huấn luyện mô hình phân loại cho biết xác suất một cảnh báo là FP dựa trên đặc trưng (như service, time, ai phát hiện...). Tiến hành **hyperparameter tuning** nếu có (SageMaker HyperParameter Tuner) để tìm tham số tốt nhất giảm FP.
*   **Cập nhật rule/threshold:** Phân tích feedback để điều chỉnh rule: ví dụ, nếu nhiều cảnh báo CPU FP khi threshold 80%, có thể nâng threshold lên 85%. Viết Lambda tự động điều chỉnh file cấu hình rule trong S3 và thông báo cho team.
*   **Triển khai mô hình mới:** Sau khi train xong, sử dụng cơ chế triển khai an toàn:
    *   Nếu dùng model ML mới, triển khai Song song (phương pháp blue-green hoặc canary): Nghĩa là giữ mô hình cũ chạy, mô hình mới chạy thử trong 10% sự kiện để so sánh.
    *   Nếu ổn định, chuyển toàn bộ sang mô hình mới, mô hình cũ retire.
    *   Việc này có thể dùng Step Function orchestration hoặc script CI/CD.
*   **Đánh giá sau cải thiện:** Thu thập số liệu **KPI** như tỷ lệ false positive trước và sau, thời gian detect trung bình, v.v. Lưu các KPI này vào báo cáo (có thể update trong README hay dashboard). Nếu có thể, thiết lập CloudWatch Alarm cho khi FP rate tăng cao bất thường (báo hiệu mô hình hoặc threshold có vấn đề).
*   **Phụ thuộc:** Phase 4 & 6 & 7 (toàn bộ pipeline phải hoạt động để có sự cố thực và phản hồi). Tuy nhiên có thể bắt đầu thiết kế feedback schema từ sớm.
*   **Tiêu chí hoàn thành:**
*   Hệ thống có cơ chế để người dùng dễ dàng gửi phản hồi sau mỗi sự cố (qua Slack hoặc giao diện). Dữ liệu phản hồi đó được lưu và sử dụng thực sự trong huấn luyện.
*   Thực hiện thành công ít nhất một vòng **retraining** mô hình hoặc cập nhật rule. Ví dụ, sau 1-2 tuần POC, thu thập 10 phản hồi, mô hình RCF được huấn luyện lại và cho kết quả giảm FP từ 10% xuống 5%.
*   Mọi thay đổi ngưỡng, mô hình được thông báo và quản lý (có version, có log). Nếu mô hình mới hoạt động kém, có cách rollback (ví dụ dễ dàng chuyển lại model cũ).
*   **Thời gian dự kiến:** 2 – 3 ngày (cho vòng đầu tiên).

### Phase 9: Batch Processing cho Knowledge Base (Tài liệu & Đồ thị tri thức)

*   **Mục tiêu:** Thiết lập quy trình **xử lý batch** cho các nguồn tài liệu và tri thức của tổ chức (như trang Confluence, wiki, cơ sở tri thức ITSM...). Mục tiêu để đảm bảo **kho tri thức** (phục vụ RCA) luôn cập nhật. Phase này tập trung vào việc tự động thu thập tài liệu từ Confluence (hoặc nguồn tương tự), làm sạch, tạo **metadata**, **embedding vector** và cập nhật **đồ thị tri thức** liên kết các thông tin quan trọng. Kết quả sẽ cải thiện khả năng tìm kiếm thông tin liên quan khi xảy ra sự cố.
*   **Thành phần AWS:**
*   **AWS Glue** hoặc **AWS Lambda** chạy theo lịch (EventBridge Schedule) để thực hiện việc crawl/xử lý tài liệu,
*   **Amazon S3** để lưu trữ nội dung tài liệu (nếu cần tải về),
*   **Vector Database** (OpenSearch, Pinecone) để lưu embedding,
*   **Graph Database** (Amazon Neptune hoặc OpenSearch Graph features) để lưu knowledge graph,
*   **Metadata Store** (có thể dùng DynamoDB hoặc OpenSearch index) để lưu thông tin mô tả tài liệu (tiêu đề, tác giả, ngày cập nhật).
*   **Phiên bản Local:**
*   Sử dụng **EventBridge** của LocalStack để mô phỏng lịch hàng ngày,
*   **Lambda** (LocalStack) hoặc một container script để gọi API Confluence (yêu cầu kết nối internet, có thể dùng API sandbox nếu có, hoặc thay bằng đọc từ file tĩnh),
*   **OpenSearch** container cho cả việc lưu embedding lẫn graph cơ bản (OpenSearch có plugin k-NN cho vector và Graph exploration cho quan hệ đơn giản).
*   **Neo4j** container cũng có thể dùng cho knowledge graph nếu OpenSearch không đủ.
*   **Các bước triển khai chính (Tasks):**
*   **Thu thập tài liệu (crawl):** Sử dụng API của Confluence (hoặc hệ thống tài liệu đang dùng) để lấy danh sách trang, chuyên mục cần thiết. Với mỗi trang: lấy nội dung (thường ở định dạng HTML hoặc wiki markup). Lưu ý phân trang nếu nhiều. Lưu nội dung thô về S3 (folder docs-raw/) để làm bản lưu.
*   **Xử lý văn bản và làm giàu metadata:** Viết một hàm xử lý nội dung tài liệu:
    *   Loại bỏ các phần không cần thiết (template, navigation).
    *   Tách văn bản thành các đoạn nhỏ hợp lý (vd mỗi heading và phần nội dung dưới nó có thể coi là một đoạn).
    *   Trích xuất metadata: tiêu đề trang, URL, tác giả, thời gian cập nhật, danh sách thẻ (labels) nếu có, liên kết giữa các trang (nếu trang A có link đến B, đó là một quan hệ tri thức).
    *   Tạo một bản ghi JSON cho mỗi đoạn: chứa nội dung đoạn (text sạch), tiêu đề trang, tiêu đề mục, author, labels, url, v.v.
    *   Lưu các bản ghi này vào S3 (folder docs-processed/, mỗi file có thể chứa nhiều đoạn từ 1 trang).
*   **Sinh embedding vectors:** Triển khai container hoặc sử dụng mô hình **Sentence Transformers** (vd all-MiniLM-L6-v2 hoặc model chuyên cho IT docs) để tạo vector cho mỗi đoạn văn bản trên. Có thể tích hợp ngay trong Lambda (nếu model nhỏ) hoặc gọi một service model. Lưu vector cùng metadata vào **Vector DB**:
    *   Nếu dùng OpenSearch: tạo index với field vector (k-NN) và các field metadata (title, labels).
    *   Nếu Pinecone/Weaviate: sử dụng SDK để upsert vectors.
*   **Xây dựng Knowledge Graph:** Dựa trên metadata và nội dung:
    *   Xác định các **thực thể (entity)** quan trọng cần cho RCA: Ví dụ: _Service_, _Component_, _Issue Type_, _Person_ (on-call), _Runbook_, _Incident_. Nhiều thông tin này có thể trích từ tài liệu (ví dụ, nếu trang Confluence thuộc không gian "Runbooks", ta coi đó là entity Runbook; nếu trang có từ khóa là tên service, có thể tạo quan hệ "Runbook liên quan Service X").
    *   Sử dụng một công cụ trích xuất đơn giản hoặc dựa vào cấu trúc: ví dụ, đặt quy ước mỗi trang runbook có trường "Applicable Services: A, B".
    *   Tạo các node tương ứng trong graph DB: Service nodes (danh sách service từ Phase 1), People nodes (từ on-call list), Document nodes (mỗi runbook), Issue nodes (loại sự cố như "CPU Spike", "Memory Leak").
    *   Tạo các **quan hệ (relationship)**:
    *   Service --(has runbook)--> Runbook,
    *   Service --(owned by)--> Team/Person,
    *   Issue Type --(documented in)--> Incident Report/Runbook,
    *   Service --(related to incident)--> Incident (post-mortem).
    *   Graph này có thể xây offline mỗi ngày một lần để không ảnh hưởng hiệu năng realtime. Lưu graph vào Neptune (trên AWS) hoặc Neo4j (local) để có thể query.
*   **Tích hợp tìm kiếm kết hợp:** Đảm bảo rằng RCA engine (Phase 6) có thể sử dụng cả vector search lẫn graph:
    *   Vector search để tìm đoạn văn bản liên quan (semantic).
    *   Graph query để tìm các mối quan hệ (ví dụ: service A liên quan đến runbook X, gợi ý runbook đó nên được xem).
*   **Kiểm thử:** Thực thi job crawl + process cho một số trang mẫu (có thể tạo vài trang Confluence giả để thử). Kiểm tra:
    *   Vector DB trả về đúng các đoạn khi truy vấn bằng keyword.
    *   Knowledge graph có thể trả lời câu hỏi đơn giản: ví dụ query "MATCH (s:Service {name:'OrderService'})-\[:HAS\_RUNBOOK\]->(r:Runbook) RETURN r" để xem các runbook của OrderService.
    *   RCA Engine khi cung cấp từ khoá service có tìm được runbook liên quan.
*   **Phụ thuộc:** Phase 6 (RCA sẽ dùng kết quả ở phase này), có thể triển khai song song sau khi định nghĩa các dịch vụ và runbook.
*   **Tiêu chí hoàn thành:**
*   **Kho tri thức** được cập nhật tự động: khi thêm một tài liệu mới hoặc cập nhật trên Confluence, trong vòng 24h hệ thống đã thu thập và nó sẵn sàng cho tra cứu.
*   Tìm kiếm **semantic** hoạt động: ví dụ tìm với truy vấn "CPU spike troubleshooting" trả về đoạn runbook hướng dẫn CPU. RCA Engine có thể lấy được đoạn liên quan trong top kết quả.
*   **Đồ thị tri thức** liên kết được các thực thể quan trọng, có thể trả lời được truy vấn quan hệ. Ví dụ: biết được service X có bao nhiêu sự cố gần đây, runbook nào liên quan, ai phụ trách.
*   Mặc dù đây là bước POC, nhưng thiết kế sẵn sàng để khi lên AWS, có thể mở rộng lưu cả nghìn tài liệu, vector search nhanh (dưới vài trăm ms).
*   **Thời gian dự kiến:** 2 – 3 ngày.

**Tổng kết timeline tham khảo cho bản POC local:**  
\- Phase 0: 1 ngày  
\- Phase 1: 2–3 ngày  
\- Phase 2: 2–3 ngày  
\- Phase 3: 2 ngày  
\- Phase 4: 4–6 ngày  
\- Phase 5: 2–3 ngày  
\- Phase 6: 3–5 ngày  
\- Phase 7: 2–3 ngày  
\- Phase 8: 2–3 ngày  
\- Phase 9: 2–3 ngày

Tổng cộng khoảng **22–32 ngày làm việc** (tầm 4–6 tuần), tùy thuộc vào độ phức tạp khi mô phỏng các thành phần ML/RCA và số lượng dịch vụ tích hợp.

## Best Practices Áp dụng Xuyên suốt

Trong quá trình thiết kế và triển khai hệ thống, chúng tôi tuân thủ nhiều **thông lệ tốt nhất** (_best practices_) để đảm bảo hạ tầng ổn định, bảo mật và dễ bảo trì:

*   **Quản lý hạ tầng bằng mã (Terraform/IaC):**
*   Mọi tài nguyên đều được tạo và quản lý bằng Terraform dưới dạng module rõ ràng theo từng domain (như đã chia ở Phase 0). Việc modules hóa giúp tái sử dụng và phân quyền dễ dàng (mỗi nhóm có thể phụ trách một module riêng).
*   **Quản lý state Terraform:** Ở môi trường local/POC, có thể dùng Terraform Cloud hoặc local backend (file) cho nhanh. Khi lên AWS, sử dụng **remote state** lưu trên S3 kết hợp khóa DynamoDB để tránh conflict khi nhiều người chạy song song. Kích hoạt mã hóa server-side cho file state (KMS) chứa thông tin nhạy cảm.
*   **Biến cấu hình & môi trường:** Sử dụng file variables hoặc workspace cho các môi trường dev/staging/prod. Các biến như is\_local, aws\_region, prefix (đặt tên), vpc\_id... được truyền phù hợp. Mỗi môi trường có tfvars riêng, đảm bảo tách biệt tài nguyên (tránh đạp lên nhau).
*   **Pin phiên bản:** Cố định phiên bản provider (AWS) và version module (nếu dùng module ngoài) để tránh thay đổi ngầm theo thời gian. Thực hiện terraform fmt và validate thường xuyên, kết hợp trong CI để duy trì code chất lượng.
*   **Hạn chế drift & tác động ngoài:** Không thay đổi hạ tầng bằng tay ngoài Terraform; nếu cần (trường hợp khẩn cấp), nhớ terraform import những tài nguyên đó về state để tránh bị xóa ngoài ý muốn khi apply lại.
*   **Bảo mật:**
*   **IAM Least Privilege:** Nguyên tắc quyền hạn tối thiểu được áp dụng. Mỗi Lambda, mỗi service chỉ được cấp quyền đúng chức năng cần thiết (ví dụ Lambda ingest chỉ cần quyền putObject S3 cho bucket raw cụ thể). Sử dụng IAM Role tách biệt cho các thành phần khác nhau, kèm theo policy boundary nếu cần giới hạn thêm.
*   **Bảo mật dữ liệu:** Mọi dữ liệu nhạy cảm lưu trên S3 hoặc database đều được mã hóa: S3 bật **SSE-KMS**, các database (OpenSearch, Redis, Neptune) bật encryption at-rest nếu trên AWS. Giao thức truyền luôn dùng TLS (HTTPS) cho kết nối giữa các dịch vụ (trên local các container giao tiếp nội bộ, khi lên AWS dùng Endpoint TLS).
*   **Mạng và VPC:** Trên AWS, triển khai các thành phần trong VPC riêng (đặc biệt với dữ liệu nhạy cảm như Redis, Neptune). Sử dụng **Private Subnet** cho các instance/database, **NAT Gateway** cho outbound an toàn, **VPC Endpoints** cho S3, KMS, DynamoDB... để lưu lượng không đi qua internet. Local thì mô phỏng đơn giản (các container trong network).
*   **Audit & Logging:** Bật **AWS CloudTrail** và AWS Config để theo dõi thay đổi cấu hình và hành vi người dùng (từ giai đoạn triển khai AWS). Lưu log của các Lambda, CloudWatch Logs group, cấu hình alarm nếu có lỗi nhiều. Secrets như API keys, webhook URL được lưu trong **AWS Secrets Manager** hoặc **SSM Parameter Store** chứ không hard-code.
*   **Khả năng mở rộng & Tối ưu chi phí:**
*   Thiết kế sẵn phương án **auto scaling**: Lambda trên AWS tự động co giãn theo concurrency (chú ý đặt limit an toàn để tránh chi phí cao bất ngờ), SageMaker Endpoint cấu hình **Auto-scaling** (tăng instance khi tải cao, giảm khi nhàn rỗi). Kinesis Stream có thể **tăng shard** nếu lưu lượng tăng. Sử dụng kiến trúc phân tán (ví dụ, có thể tách nhiều stream theo nhóm service để scale riêng).
*   Tối ưu lưu trữ S3: bật **nén dữ liệu** (ví dụ log lưu ở định dạng Parquet hoặc gzip JSON để giảm dung lượng), thiết kế **partition phù hợp** (tránh partition quá nhỏ gây quá nhiều file).
*   Với workload batch (như training ML), xem xét dùng **Spot Instances** trên AWS để tiết kiệm, kết hợp cơ chế checkpoint để resume nếu bị gián đoạn. Với dịch vụ luôn chạy (như OpenSearch), cân nhắc instance phù hợp, hoặc dùng **Serverless** option nếu có để tự động scale theo tải.
*   Thiết lập **AWS Budgets/Alerts** để giám sát chi phí hàng tháng, tránh vượt ngân sách.
*   **Quan sát/giám sát (Observability):**
*   **Logging & Monitoring:** Mỗi thành phần (Lambda, container, Spark job) đều được cấu hình log chi tiết (sử dụng CloudWatch Logs hoặc volume log với container local). Đặt các **metric** giám sát pipeline: ví dụ độ trễ trung bình từ ingest đến detection, số lượng anomaly phát hiện mỗi ngày, dung lượng data pipeline.
*   **Alerts nội bộ:** Thiết lập cảnh báo cho chính hệ thống giám sát: nếu thành phần nào lỗi (ví dụ Lambda error rate tăng, bước ETL thất bại, queue tồn đọng nhiều), gửi cảnh báo cho đội phát triển hệ thống để khắc phục kịp thời.
*   **Distributed Tracing:** Trên AWS, tận dụng **AWS X-Ray** để theo dõi luồng qua các Lambda/Step Functions (giúp debug hiệu năng, phát hiện nút thắt cổ chai). Ở local, có thể tích hợp OpenTelemetry cho các dịch vụ chính để log traceID nếu cần.
*   **Thiết kế ứng dụng & Code:**
*   Xác định **hợp đồng (contract)** rõ ràng cho các sự kiện trao đổi giữa các thành phần. Ví dụ: định nghĩa JSON schema cho sự kiện anomaly.confirmed (chứa những field gì), sự kiện anomaly.rca.ready (bao gồm những thông tin gì). Việc này giúp các team khác (nhận alert, hay dùng data) hiểu rõ và tích hợp dễ dàng, đồng thời tránh lỗi do hiểu sai định dạng.
*   Đảm bảo **idempotency** và **retry**: Mọi xử lý nên thiết kế để nếu lặp lại cũng không gây lỗi (ví dụ Lambda consumer đọc Kinesis nên sẵn sàng xử lý trùng nếu kinesis retry, nhờ kiểm tra unique ID của event). Sử dụng DLQ (Dead Letter Queue) cho mọi tiến trình tiêu thụ (Lambda, Queue) để không mất sự kiện khi lỗi. Áp dụng chiến lược backoff khi retry để không gây quá tải (ví dụ exponential backoff).
*   **Versioning:** Đối với mô hình ML và runbook, thực hiện quản lý phiên bản. Mỗi khi cập nhật mô hình mới, gán version (vd v2.0) và lưu song song model cũ để rollback khi cần. Các runbook thay đổi cũng nên lưu lịch sử (Confluence có sẵn version).
*   **Testing:** Viết test cho các hàm xử lý quan trọng (đặc biệt phần logic detection, RCA). Trên local có thể viết unit test chạy trực tiếp (không qua Lambda) để đảm bảo thuật toán đúng. Mỗi khi điều chỉnh threshold hoặc logic, chạy lại test trên tập dữ liệu mẫu để so sánh kết quả.
*   **Chuyển đổi môi trường linh hoạt:**
*   Tất cả các URL endpoint, tên tài nguyên đều tham chiếu qua biến hoặc config – không hard-code – để đảm bảo khi chuyển từ local sang AWS thật chỉ cần thay giá trị config.
*   Phân tách rõ code dành cho môi trường local và code cho AWS bằng điều kiện hoặc module riêng. Ví dụ: phần gọi Bedrock trên AWS sẽ thay bằng gọi API local trong chế độ local, được bao bởi if is\_local ....
*   Kích hoạt/tắt một số tính năng tùy môi trường (feature toggle). Ví dụ: có thể tắt hẳn RCA AI trên local nếu không đủ tài nguyên, thay vào đó trả về mẫu dummy; nhưng trên AWS thì bật đầy đủ. Điều này giúp POC đơn giản hơn mà vẫn kiến trúc chuẩn bị sẵn.

## Rủi ro và Phương án Giảm thiểu

Khi thực hiện dự án, nhóm đã xác định một số rủi ro tiềm tàng và đề ra hướng giảm thiểu:

*   **Hạn chế của LocalStack:** Không phải tất cả dịch vụ AWS đều được LocalStack hỗ trợ hoặc hỗ trợ đầy đủ. Đặc biệt: Bedrock, SageMaker, Timestream, ElastiCache, App Mesh, CloudWatch Dashboards hiện không có hoặc rất hạn chế trên LocalStack.
*   _Mitigation:_ Như kế hoạch đã nêu, chúng tôi sử dụng cách tiếp cận _mô phỏng_ với các dịch vụ thay thế: container LLM cho Bedrock, tích hợp mô hình thẳng trong Lambda thay SageMaker, dùng Redis container thay ElastiCache, v.v. Chúng tôi cũng thiết kế interface chung để sau này chuyển sang AWS dễ dàng: ví dụ, xây một lớp trừu tượng cho **ModelInference**; local thì gọi hàm nội bộ, AWS thì gọi endpoint SageMaker.
*   Ngoài ra, chấp nhận rằng một số tính năng nâng cao (như CloudWatch Dashboard xịn) sẽ chỉ làm khi lên AWS, còn POC thì làm đơn giản (Grafana). Tài liệu sẽ ghi rõ những khác biệt này để khách hàng/đội ngũ hiểu.
*   **Độ trễ và hiệu năng trong môi trường local:** Chạy mọi thứ trên một máy dev có giới hạn CPU/RAM, Docker nhiều container có thể chậm, đặc biệt khi chạy mô hình ML lớn hay OpenSearch trên laptop.
*   _Mitigation:_ Giới hạn quy mô demo: ví dụ chỉ chạy một vài service giả lập, giảm tần suất log (một vài trăm events/s thay vì hàng nghìn nếu máy không kham nổi). Điều chỉnh kích thước mô hình (dùng mô hình nhỏ hơn, ít dữ liệu hơn cho vector DB). Quan trọng là chứng minh được kiến trúc, thông số hiệu năng thực sẽ đo trên AWS thật với cơ sở hạ tầng mạnh.
*   Ngoài ra, có thể tách bớt một số thành phần ít liên quan khỏi máy local, ví dụ sử dụng dịch vụ Managed miễn phí/tier thấp trên cloud trong giai đoạn POC (như Pinecone free tier cho vector, hay một endpoint SageMaker nhỏ) nếu cần giảm tải cho local.
*   **Độ chính xác của mô hình phát hiện bất thường:** Ban đầu do thiếu dữ liệu nhãn, mô hình ML unsupervised có thể cho nhiều false positive, gây mất niềm tin người dùng.
*   _Mitigation:_ Kết hợp phương pháp rule-based như lưới an toàn: ví dụ chỉ khi vượt ngưỡng rõ ràng mới cảnh báo, tránh trường hợp model báo lung tung. Triển khai threshold và logic bảo thủ lúc đầu. Sau đó dần dần nới lỏng khi có feedback cải thiện.
*   Tăng cường thu thập dữ liệu và gắn nhãn sớm (dù ít nhưng chất lượng) để tinh chỉnh model. Sử dụng kỹ thuật **transfer learning** từ những model anomaly phổ biến (như pre-trained RCF) để có baseline tốt. Feedback loop (Phase 8) là chìa khóa: liên tục học từ sai sót để giảm FP.
*   **Độ tin cậy của topology và RCA:** Nếu không có dữ liệu thực (traces, incidents thực tế), việc mô phỏng topology có thể không sát thực tế, RCA có thể đoán sai vì thiếu thông tin.
*   _Mitigation:_ Lưu ý người dùng rằng POC dùng cấu hình tĩnh, khi triển khai thật cần tích hợp APM/Tracing để có ảnh thật. Với RCA, bắt đầu từ rule-based và knowledge base đơn giản (ví dụ map lỗi "OutOfMemory" -> nguyên nhân thiếu memory) để ít nhất có một số kết quả đúng hiển nhiên. Từng bước nâng cấp độ phức tạp của RCA khi có đủ dữ liệu và tài liệu.
*   Cũng có thể thực hiện một số **scenario test**: chuẩn bị sẵn vài kịch bản sự cố thường gặp và kiểm tra RCA có xử lý được không, tinh chỉnh trước khi go-live.
*   **Tích hợp bên thứ ba (Slack/Jira/PagerDuty):** Các API này có hạn mức (rate limit) hoặc yêu cầu xác thực chặt, có thể khó thử nghiệm.
*   _Mitigation:_ Sử dụng **environment sandbox**: Slack có workspace dev, PagerDuty có chế độ training, Jira có project test. Thiết lập throttle ở hệ thống của mình: ví dụ không gửi quá 1 thông báo/giây đến Slack để tránh bị chặn.
*   Chuẩn bị sẵn phương án fallback: nếu gửi đến Slack lỗi, có thể thử gửi email thay thế, hoặc ít nhất log rõ để sau xử lý.
*   Bảo mật webhook URL và token trong secrets, tránh lộ ra ngoài.

Ngoài ra, nhóm luôn có kế hoạch **kiểm thử** ở mỗi phase để phát hiện sớm vấn đề (sẽ nói rõ hơn ở phần kiểm thử), nhờ đó giảm thiểu rủi ro tích tụ.

## Kế hoạch Chuyển tiếp sang AWS Thật

Sau khi hoàn thiện POC trên local và xác minh kiến trúc hoạt động, bước tiếp theo là triển khai hệ thống lên môi trường AWS thật (dev/staging, rồi prod). Quá trình này cần chuẩn bị kỹ càng để chuyển đổi suôn sẻ từ các thành phần giả lập sang dịch vụ thật, đồng thời đảm bảo các yêu cầu về mạng, bảo mật, hiệu năng trên AWS. Dưới đây là hướng dẫn tổng quan:

**Chuẩn bị tài khoản và hạ tầng chung:**  
\- Thiết lập các tài khoản AWS cho dev/staging/prod. Cấu hình quyền (AWS IAM) cho team triển khai, tốt nhất sử dụng AWS SSO hoặc IAM Role cho CI/CD.  
\- Tạo trước một S3 bucket (global) dùng làm **Terraform backend** và một DynamoDB table cho khóa state (nếu chưa có từ phase 0). Thiết lập backend này trong code Terraform (backend "s3").  
\- Tạo các **KMS keys** cần thiết: một key để mã hóa S3 bucket, một key để mã hóa secret nếu dùng. Phân quyền cho các dịch vụ (thông qua IAM) được sử dụng key này.

**Triển khai theo từng Phase trên AWS:**

*   **Phase 1 (Data Sources & Ingestion):**
*   Tạo **Kinesis Data Streams** (chính thức) thay cho Kinesis Local. Cân nhắc nếu lượng log rất lớn, có thể dùng **Amazon MSK (Managed Kafka)** để tương thích hệ sinh thái Kafka.
*   Thiết lập **Kinesis Data Firehose**: tạo Delivery Stream lấy nguồn từ Kinesis (hoặc từ trực tiếp CloudWatch Logs) đưa vào S3. Cấu hình chuyển đổi (như nén GZIP, partition theo thời gian) nếu cần.
*   Kết nối **CloudWatch Logs**: trong các tài khoản AWS, có thể tạo **Subscription Filter** để chuyển log từ CloudWatch (của các Lambda khác hoặc EC2) vào Kinesis stream. Nếu ứng dụng gửi metric vào CloudWatch, có thể dùng **CloudWatch Metric Stream** tới Kinesis Firehose.
*   Bảo đảm S3 raw bucket có gắn chính sách đúng (Policy cho Firehose được PutObject). Bật **Server Access Logging** nếu cần audit truy cập.
*   **Phase 2 (ETL & Data Catalog):**
*   Tạo **Glue Data Catalog Database** và **Glue Crawlers** cho các bucket raw và transformed. Chạy crawler để nó tạo bảng schema.
*   Chuyển Spark job thành **Glue Job**: upload script lên S3, cấu hình Glue Job với IAM Role thích hợp (quyền đọc bucket raw, ghi bucket transformed, update catalog). Chạy thử job trên AWS Glue (dev endpoint) với một lượng dữ liệu nhỏ để hiệu chỉnh.
*   Nếu data lớn, có thể dùng cluster Glue với số worker phù hợp. Bật **Glue Job Bookmark** để nó nhớ đã xử lý đến partition nào, tránh xử lý trùng.
*   Kích hoạt **Athena**: tạo vài **Athena views** hoặc query thông qua AWS Console để đảm bảo Data Catalog hoạt động.
*   **Phase 3 (Storage hot/cold):**
*   Triển khai **Amazon ElastiCache Redis**: tạo một cluster Redis (ví dụ cache.t3.small cho dev), Multi-AZ if prod. Cấu hình parameter group (nếu cần tăng maxmemory, LRU eviction). Cho Redis chạy trong VPC, subnet private.
*   Triển khai **Amazon Timestream** nếu sử dụng: tạo database và table, với cấu hình TTL cho memory store và magnetic store (ví dụ data 1 ngày ở memory, 1 năm ở magnetic). Nếu không dùng Timestream, có thể skip.
*   Thiết lập **Athena/Redshift Spectrum**: tạo catalog cho data trên S3. Nếu dùng Redshift Spectrum, tạo cluster Redshift (hoặc serverless) và định nghĩa external schema.
*   Chuyển cơ chế cập nhật Redis: dùng **Lambda** (hoặc Kinesis Data Analytics) để đọc stream và ghi Redis. Trên AWS, Lambda có thể tiếp nhận Kinesis event batch dễ dàng. Bảo đảm cấu hình VPC cho Lambda để có access Redis (vì Redis trong VPC).
*   Kiểm tra tốc độ: có thể dùng Amazon CloudWatch metrics cho Lambda (iterator age) để xem việc đẩy redis có bị trễ không.
*   **Phase 4 (Detection & Decision on AWS):**
*   Triển khai các Lambda function (statistical, rule-based) lên AWS: viết code trong AWS Lambda (Python/Node...) và deploy (Terraform có thể zip code hoặc sử dụng image). Gán đủ IAM (ví dụ quyền đọc Redis, quyền get dữ liệu S3...).
*   Chuẩn bị dữ liệu và train model ML: sử dụng **Amazon SageMaker** để train model RCF hoặc anomaly detection model khác nếu chưa có. Amazon cung cấp sẵn **RandomCutForest** algorithm – có thể dùng dịch vụ **SageMaker JumpStart** để lấy model anomaly detection. Train với data sample, deploy model thành **SageMaker Endpoint** ( chọn instance CPU hoặc GPU nhỏ cho dev). Lưu lại endpoint name.
*   Tích hợp vào **Step Functions**: xây dựng State Machine với các bước Parallel cho Lambda Stats, Lambda Rule, Lambda Invoke Endpoint (SageMaker). Step Functions trên AWS có sẵn integration với SageMaker endpoint (InvokeEndpoint). Kịch bản: StepFunction lấy input (service+metric), chuyển đến 3 nhánh, đợi kết quả, sau đó Task cuối gọi Lambda Decision để hợp nhất.
*   Cấp quyền cho Step Functions: IAM Role của Step Functions được phép invoke Lambda và SageMaker endpoint.
*   Kích hoạt detection theo lịch: có thể dùng **EventBridge Rule** mỗi phút để khởi chạy Step Function cho từng metric cần theo dõi. Hoặc dùng Lambda scheduler bên trong (ít nên làm).
*   Test end-to-end: gửi một loạt dữ liệu bất thường lên dev, xem Log CloudWatch của Step Functions (hoặc AWS X-Ray trace) để kiểm tra các bước.
*   **Phase 5 (Topology on AWS):**
*   Bật **AWS X-Ray** cho các ứng dụng microservice (nếu có ứng dụng chạy thực). X-Ray sẽ tự vẽ service map. Trong POC dev, có thể tạo một script giả lập segment X-Ray (khó, nên có thể trì hoãn).
*   Triển khai **AWS Neptune**: nếu có nhu cầu lưu đồ thị dài hạn. Neptune cần VPC, nên tạo cluster trong VPC. Import dữ liệu (nếu có sẵn file). Nếu không, có thể dùng chính OpenSearch Graph hoặc AWS Resource Graph (nếu leverage tagging) – tuỳ tình huống.
*   Sử dụng **AWS Application Discovery Service / Service Catalog** nếu có để nhập thông tin kiến trúc.
*   Thực tế, trên AWS sản phẩm, topology có thể được xây từ nhiều nguồn: code deploy, Kubernetes service mesh, etc. Cho POC, Neptune có thể làm quá, có thể chỉ dùng file.
*   **Phase 6 (RCA on AWS):**
*   Tích hợp với **Amazon Bedrock**: đăng ký dịch vụ Bedrock, sử dụng API (quá trình này cần AWS cho phép). Nếu Bedrock chưa GA hoặc không sẵn, có thể dùng **OpenAI API** hoặc **Anthropic API** qua gateway. Tuy nhiên, để tuân thủ AWS, Bedrock với model Titan, hoặc dùng **SageMaker JumpStart** LLM (if available) cũng được. Triển khai một Lambda gọi đến Bedrock endpoint với prompt.
*   Sử dụng **Amazon OpenSearch Serverless** cho vector: tạo domain OpenSearch, bật plugin k-NN. Index vector đã có (có thể re-index từ đầu hoặc upload).
*   Confluence integration: có thể chạy thực luôn, nhưng cần đảm bảo bảo mật (token API).
*   Chú ý giới hạn: Bedrock và OpenSearch đều tốn tiền, nên dev environment có thể hạn chế số tài liệu hoặc call.
*   Kiểm tra: tạo một anomaly test và chạy RCA Lambda, xem log để thấy truy vấn vector và LLM trả về.
*   **Phase 7 (Alerting on AWS):**
*   Tạo **SQS queues**: e.g. alert-critical, alert-normal, kèm DLQ. Configure redrive policy.
*   Tạo **SNS topics/Subscriptions** nếu dùng (ví dụ SNS -> Email for certain alerts).
*   Slack: tạo Slack App, lấy token OAuth và webhook URL. Lưu trong **AWS Secrets Manager**. Tương tự lưu API key cho PagerDuty, Jira.
*   Triển khai Lambda Alert Manager (như Phase 7): cho phép nó truy cập Secrets (via env var or direct Secrets Manager API).
*   CloudWatch Alarms: có thể tích hợp SNS để test email alerts.
*   CloudWatch Dashboard: tạo một Dashboard JSON with widgets for key metrics (error count, anomalies, system health) – deploy via Terraform.
*   Test: kích hoạt một fake anomaly, check Slack channel real, PagerDuty incident if any.
*   **Phase 8 (Feedback & Learning on AWS):**
*   Tạo **API Gateway + Lambda** for feedback, if interactive (or could use simple web UI in cloud).
*   Tạo **DynamoDB table** Feedback (with incident\_id as key) to store quick lookup, in addition to S3 logging.
*   Use **AWS Glue** to join anomaly data and feedback for training dataset.
*   Use **SageMaker** training job to retrain model, similar as earlier. Possibly integrate with CI/CD: e.g. commit new model artifact to S3, trigger pipeline to deploy it.
*   Implement automatic threshold tuning Lambda: e.g. runs weekly to adjust parameters stored in SSM Parameter Store.
*   Ensure proper approvals for deploying new model in production (maybe require manual review if needed).
*   **Phase 9 (Docs processing on AWS):**
*   Use **EventBridge Scheduler** for daily triggers.
*   Use **Lambda** for crawl and processing to avoid maintaining EC2. If docs large, consider **AWS Batch** or **Fargate** for heavy embedding tasks.
*   Use **Comprehend** or other NLP services if needed to extract entities from text (could be an enhancement).
*   Neptune: if using Neptune for knowledge graph, commit the graph updates via Neptune Bulk Loader or via Gremlin queries in Lambda. Neptune is SPARQL/Gremlin, might require VPC access.
*   Test search: using OpenSearch search API with queries, ensure results are relevant.

**Kiểm thử và dữ liệu khi chuyển môi trường:**  
\- Trước khi chuyển, **seed dữ liệu**: có thể lấy một mẫu dữ liệu từ môi trường local (S3 raw logs vài MB) upload lên S3 dev để có cái mà thử. Tương tự, có thể nạp một số giả lập anomaly để test pipeline.  
\- **Kiểm thử tích hợp từng phần:** Không đẩy lên tất cả rồi mới test, mà sau mỗi cụm dịch vụ trên AWS, chạy thử. Ví dụ: test ingestion + S3 (Phase 1) xong mới qua ETL (Phase 2). Dùng dữ liệu giả nhỏ cho mỗi test.  
\- **Theo dõi chi phí:** Bật CloudWatch Billing alarm, dùng AWS Cost Explorer để thấy dịch vụ nào tốn nhiều (đặc biệt chú ý OpenSearch, Bedrock, SageMaker).  
\- **Tài liệu vận hành:** Cập nhật wiki nội bộ với hướng dẫn triển khai mới (ví dụ, cách truy cập Neptune console, cách update Slack webhook if changed).

**Rollback và Bảo trì:**  
\- Mỗi phase khi triển khai AWS cần có kế hoạch rollback: ví dụ nếu Phase 4 (detection) gặp sự cố làm tốn chi phí, có thể tắt các Lambda scheduler đi (EventBridge rule disable) trong thời gian debug. Terraform cho phép destroy module nếu cần revert.  
\- Sử dụng **feature toggle**: ví dụ nếu RCA chưa ổn định, có thể tắt flag để hệ thống chỉ gửi alert thô (không tự động RCA) nhằm không cản trở vận hành.  
\- **Bảo trì định kỳ:** Xây dựng lịch bảo trì cho các thành phần như: Xoá log cũ trên CloudWatch để tiết kiệm, xoá index cũ OpenSearch (nếu có), update định kỳ AMI cho Lambda container để đảm bảo bảo mật.

**Khác biệt đáng chú ý khi lên AWS thật:**  
\- Chủ yếu là về **mạng và bảo mật**: Local mọi thứ mở, AWS cần chú ý VPC, Security Group, IAM cho từng lambda, v.v.  
\- Tính **thực tế dữ liệu**: Ở AWS, logs thật có thể lộn xộn và nhiều loại không lường trước, cần robust parsing hơn so với data giả lập "đẹp" ở local.  
\- **Quan sát hệ thống**: trên AWS có đầy đủ CloudWatch metrics, X-Ray, nên tận dụng triệt để để theo dõi hệ thống khi vận hành thật (cái này local thiếu).  
\- **Chi phí**: Môi trường thật phải luôn cân bằng giữa hiệu năng và chi phí, có thể phải điều chỉnh một số dịch vụ: ví dụ ban đầu không dùng Neptune (tốn kém) mà dùng OpenSearch multi-modal cho graph + vector, hoặc thay Bedrock (hiện mới, có thể đắt) bằng cách khác nếu ngân sách hạn chế.

## Công cụ và Công nghệ Sử dụng

Trong dự án này, chúng tôi sử dụng nhiều công cụ để hỗ trợ phát triển, giả lập và triển khai:

*   **LocalStack:** Nền tảng giả lập dịch vụ AWS, cho phép chạy hầu hết dịch vụ AWS cơ bản trên máy local. LocalStack được dùng để test S3, Kinesis, Lambda, SQS, EventBridge, Step Functions, DynamoDB, SNS/SNS, CloudWatch Logs cơ bản... Lợi ích là có thể phát triển và chạy thử pipeline mà không cần AWS thật, nhanh và không tốn chi phí.
*   **Docker & Docker Compose:** Để chạy các thành phần không có trên LocalStack, chúng tôi sử dụng Docker containers:
*   **Redis**: Mô phỏng ElastiCache Redis cho cache nóng.
*   **OpenSearch**: Mô phỏng Amazon OpenSearch (ElasticSearch) cho cả hai mục đích: làm search engine (nếu cần text search log) và vector database (sử dụng k-NN plugin) phục vụ RCA.
*   **Neo4j**: Cơ sở dữ liệu đồ thị để lưu topology và knowledge graph ở local.
*   **Spark**: (Tùy chọn) container Spark hoặc Hadoop để làm ETL nếu Glue không chạy local.
*   **Grafana**: giao diện dashboard để xem metric và alert (một giải pháp thay thế CloudWatch Dashboards).
*   **Kafka (Redpanda)**: nếu cần mô phỏng MSK, có thể dùng Redpanda (Kafka written in C++) chạy gọn nhẹ trong container.
*   **Terraform:** Công cụ IaC chính để quản lý tất cả tài nguyên. Sử dụng Terraform cả cho local (với endpoint LocalStack) lẫn AWS. Việc này giúp cấu hình hạ tầng nhất quán và dễ theo dõi thay đổi. Terraform module cho phép chia nhỏ cấu hình theo chức năng.
*   **AWS CLI & AWS CDK (nếu cần):** AWS CLI được dùng để kiểm tra nhanh các dịch vụ khi cần (ví dụ liệt kê S3 object trên localstack hoặc AWS). AWS CDK không sử dụng trong triển khai chính (vì chọn Terraform), nhưng có thể dùng tạm cho một số script tạo dữ liệu giả nếu nhanh hơn.
*   **CI/CD:** Sử dụng hệ thống CI (GitHub Actions hoặc GitLab CI) để tự động hóa kiểm tra Terraform, chạy test cho code Lambda (nếu có). Triển khai môi trường AWS có thể thông qua pipeline (môi trường dev -> staging -> prod, phê duyệt nếu cần).
*   **Ngôn ngữ & thư viện:**
*   Code Lambda dự kiến dùng **Python** (thuận tiện cho xử lý dữ liệu, ML) và **Node.js** (thuận cho Slack integration).
*   Các thư viện nổi bật: boto3 (AWS SDK for Python), pandas/numpy cho xử lý số liệu, scikit-learn hoặc statsmodels cho thuật toán thống kê, aws-lambda-powertools (giúp best practice cho Lambda logging, metrics).
*   Mô hình ML: có thể dùng sagemaker SDK để dễ deploy/training trên AWS. Mô hình LLM có thể dùng transformers của HuggingFace (nếu xài local model).

Tất cả những công cụ trên kết hợp lại tạo thành một môi trường phát triển và triển khai hiện đại, cho phép chúng tôi xây dựng hệ thống một cách nhanh chóng, thử nghiệm an toàn trước khi lên cloud thật, đồng thời tận dụng sức mạnh các dịch vụ AWS khi sẵn sàng.

## Hướng dẫn Kiểm thử Tổng quát

Sau khi hoàn thành các phase, việc kiểm thử tích hợp end-to-end và theo từng phần là rất quan trọng. Dưới đây là hướng dẫn kiểm thử hệ thống cả ở chế độ local và khi lên AWS (chú trọng kiểm thử luồng chính, không đi sâu vào lệnh cụ thể):

**Kiểm thử trên môi trường Local (POC):**

1.  **Khởi động toàn bộ môi trường local:** Chạy LocalStack (đảm bảo các dịch vụ cần thiết đã bật, như SERVICES=kinesis,s3,lambda,...), sau đó chạy docker-compose up (hoặc lệnh tương ứng) để bật Redis, OpenSearch, Neo4j, Grafana... Chờ các container lên hoàn toàn, xem log để chắc chắn không có lỗi (đặc biệt OpenSearch cần chút thời gian để ready).
2.  **Triển khai hạ tầng bằng Terraform:** Chạy terraform apply -var="is\_local=true" với các tfvars cho môi trường local. Kiểm tra output đảm bảo các resource (giả lập) được tạo (ví dụ log trong LocalStack cho thấy đã tạo S3 bucket, Lambda...).
3.  **Test luồng Data Ingestion (Phase 1):**
4.  Thực thi Lambda generator (có thể invoke nó vài lần hoặc nó tự chạy theo lịch).
5.  Dùng AWS CLI (trỏ LocalStack) aws kinesis list-streams xem stream có dữ liệu không (có thể add code log trong Lambda consumer để thấy nhận được record).
6.  Kiểm tra S3 bucket raw: dùng AWS CLI aws s3 ls trên localstack endpoint xem file đã được tạo chưa. Mở file (s3 cp về) kiểm tra nội dung JSON đúng format.
7.  **Test ETL (Phase 2):**
8.  Kích hoạt job ETL (có thể là chạy spark-submit nếu dùng Spark local). Đảm bảo job chạy không lỗi.
9.  Kiểm tra S3 bucket transformed: xem có thư mục ngày/tháng, file output.
10.  Nếu có Glue catalog mock, kiểm tra file schema output (nếu có). Có thể thử dùng Trino/Presto (nếu đã thiết lập) để query file Parquet, so sánh kết quả với raw ban đầu để chắc transform đúng.
11.  **Test Hot storage (Phase 3):**
12.  Sau khi có pipeline ingest liên tục, kiểm tra trong Redis: kết nối tới Redis container (dùng redis-cli) xem các key metrics:\* có tồn tại không. Lấy một key, dùng lệnh LRANGE (nếu dùng list) để xem có giá trị gần nhất. Đối chiếu với S3 raw xem có khớp.
13.  (Nếu có Timestream giả lập, có thể kiểm tra trong DB đó, nhưng khả năng thấp do Timestream local bỏ qua).
14.  **Test Detection Engine (Phase 4):**
15.  Cấu hình một tình huống cụ thể: ví dụ sửa Lambda generator để tạo một đợt spike CPU rõ (cho CPU = 95 liên tục 1 phút).
16.  Quan sát log của Lambda thống kê và ML (LocalStack cho phép xem CloudWatch Logs - có thể tích hợp awslocal logs tail). Xem các Lambda có log "Anomaly detected" hay không.
17.  Xem log của Decision Lambda (hoặc Step Functions): đảm bảo nó nhận đủ kết quả từ các nhánh. Nếu có output ra S3 anomalies/, lấy file đó kiểm tra nội dung.
18.  Kiểm tra thời gian: nhìn timestamp log, từ lúc sự kiện spike đến lúc anomaly.confirmed log xuất hiện, xem có <5s không, nếu > có thể tối ưu lại tham số.
19.  **Test Topology (Phase 5):**
20.  Tạo một sự cố và xem Lambda update topology (nếu có): Kiểm tra trong Neo4j: mở Neo4j Browser (http://localhost:7474) chạy câu truy vấn để xem node OrderService có status "critical"? Các node liên quan có status "warning"?
21.  Mở trang topology (nếu có tạo web): xem đồ thị hiển thị, đối chiếu với mong đợi (node màu đỏ, các node láng giềng màu vàng, tên dịch vụ đầy đủ).
22.  Thử thay đổi file cấu hình quan hệ (giả lập thêm một dependency) rồi reload xem có update chính xác.
23.  **Test RCA (Phase 6):**
24.  Với sự cố đã tạo (spike CPU), gọi RCA service (có thể nó tự triggered, hoặc trigger bằng tay event anomaly.confirmed).
25.  Xem log RCA (nếu có): có các bước retrieval tài liệu không, có lỗi kết nối OpenSearch không.
26.  Kiểm tra output RCA: lấy file JSON output trên S3 anomaly\_rca/, xem nội dung. Nó có trường root\_cause\_hypothesis, recommended\_actions... không?
27.  Đánh giá logic: ví dụ trong case CPU spike, RCA có nói "có thể do load tăng hoặc code loop" chẳng hạn, và khuyến nghị "kiểm tra deployment gần đây". Nếu output quá sơ sài, có thể tinh chỉnh thêm prompt hay logic.
28.  **Test Alerting (Phase 7):**
29.  Kiểm tra SQS queue: xem có message khi RCA xong không (LocalStack SQS có thể poll).
30.  Xem log Lambda gửi Slack: có thành công không (nếu Slack API key dùng dev workspace, xem kênh Slack nhận được chưa).
31.  Thử nút Acknowledge: bấm trong Slack (nếu đã code interactive), có thể gởi một request fake tới endpoint local ngắn gọn. Xem log webhook Lambda để chắc nhận được.
32.  Kiểm tra Jira: đăng nhập Jira dev xem có ticket mới.
33.  Mở Grafana: xem biểu đồ có highlight lúc 13:33 CPU spike, có danh sách alert nào (có thể dùng Grafana Alertmanager hoặc plugin).
34.  Đánh giá toàn diện: người dùng cuối (giả lập) nhận được thông báo, đọc nội dung, thấy đủ thông tin và có thể hành động theo.
35.  **Test Feedback (Phase 8):**
    *   Mở giao diện feedback (nếu có) hoặc dùng curl gửi một mẫu feedback cho incident vừa xảy ra.
    *   Kiểm tra S3 feedback/ có file ghi lại. Mở file xem format đúng.
    *   Chạy job training (nếu có) với dataset nhỏ (có thể script offline). Xem log training, kiểm tra model artifact output (nếu có).
    *   Giả lập thay đổi threshold: ví dụ giảm threshold CPU trong config, xem lần sau hệ thống có ít cảnh báo CPU false hơn không (có thể cần nhiều data hơn cho rõ nhưng conceptually).
36.  **Test Knowledge Base (Phase 9):**
    *   Chạy crawler Confluence (nếu tích hợp internet sandbox, nếu không, skip).
    *   Kiểm tra S3 docs-processed có file chứa nội dung tài liệu. Mở xem có text, metadata đẹp không.
    *   Kiểm tra vector DB: dùng API search (OpenSearch Dev console) với một câu truy vấn, xem kết quả.
    *   Kiểm tra knowledge graph: chạy query trong Neo4j xem có node, quan hệ đúng như parse từ tài liệu không (ví dụ runbook X liên quan service Y).
    *   Đảm bảo RCA (phase 6) có thể kết nối tới vector DB (thử lại RCA nếu cần, xem log có tìm thấy doc và chèn vào prompt).
37.  **Test tình huống tổng thể (End-to-End):**
    *   Để kết thúc, làm một cuộc diễn tập nhỏ: Giả định một service mới deploy gây ra lỗi. Tạo các log, metric tương ứng (có thể viết một script tạo scenario, hoặc làm thủ công: push log error, set metric xấu).
    *   Theo dõi toàn hệ thống phản ứng: detection -> anomaly -> RCA -> alert.
    *   Đảm bảo mọi thành phần vận hành trơn tru, kết quả cuối đến được tay "người vận hành" (trong Slack/Jira).
    *   Thu thập số liệu: Thời gian tổng từ lúc bắt đầu đến lúc alert là bao lâu? Thông tin missing gì không?
    *   Ghi nhận những cải thiện muốn làm nếu có thêm thời gian.

**Kiểm thử trên môi trường AWS thực:**

Khi chuyển sang AWS, cần lặp lại các bước kiểm thử tương tự, nhưng chú trọng thêm: - Kiểm tra cấu hình mạng (ví dụ Lambda trong VPC có kết nối được Redis/Neptune? Security Group có mở port đúng?). - Hiệu năng lớn: dùng AWS Benchmark tool (ví dụ Kinesis Producer Library) bơm nhiều data để xem hệ thống chịu tải, monitor CloudWatch metrics (Lambda duration, Throttles, Kinesis IteratorAge...). - Test failover: ví dụ tắt 1 AZ (nếu có multi-AZ) xem hệ thống còn hoạt động (nhất là Redis cluster). - Test độ bền: restart Neptune/OpenSearch node (nếu cluster) để xem graph và vector DB vẫn ok.

Tuy các bước kiểm thử phức tạp, nhưng tuân thủ chúng sẽ giúp đảm bảo hệ thống không chỉ chạy được trong lý thuyết mà thực sự vững chắc trong thực tế.

## Ví dụ Minh họa Triển khai Một Tác vụ Mẫu (Phase 1)

_(Phần này cung cấp một ví dụ cụ thể cách thực hiện một tác vụ trong Phase 1 để bạn đọc dễ hình dung. Lưu ý đây chỉ là minh họa, không bao gồm mã nguồn chi tiết.)_

**Tác vụ:** _Tạo S3 bucket raw và luồng Kinesis → S3 để tiếp nhận log._

**Các bước triển khai:**

1.  _Chuẩn hóa cấu hình:_ Trước hết, đảm bảo trong file cấu hình Terraform có các biến cần thiết, ví dụ: project\_name, env, enable\_kinesis\_to\_s3. Biến is\_local có thể được dùng để quyết định dùng Kinesis Firehose hay Lambda tự viết.
2.  _Tạo S3 bucket (raw logs):_ Viết Terraform cho resource aws\_s3\_bucket:
3.  Tên bucket tuân theo quy tắc: ví dụ ${var.project\_name}-${var.env}-raw-logs.
4.  Bật versioning (phòng khi cần khôi phục dữ liệu bị ghi đè).
5.  Bật server\_side\_encryption với KMS (chỉ AWS).
6.  Gắn tag chuẩn (Environment, Project...).
7.  Thiết lập policy cho phép dịch vụ Kinesis Firehose (nếu AWS) có thể put object vào bucket. Cụ thể, thêm một statement trong bucket policy: Principal là Firehose service, Action "s3:PutObject", Resource bucket/\*.
8.  _Tạo Kinesis stream:_ Resource aws\_kinesis\_stream:
9.  Name: ${var.project\_name}-${var.env}-logs-stream.
10.  Shard count: đặt 1 hoặc 2 cho dev.
11.  Retention: để mặc định 24h (hoặc 72h nếu log quan trọng).
12.  Tags đầy đủ.
13.  _Thiết lập luồng đẩy vào S3:_
14.  **Trên AWS thực:** Tạo aws\_kinesis\_firehose\_delivery\_stream:
    *   Source: Kinesis stream trên.
    *   Destination: S3 bucket raw đã tạo.
    *   Thiết lập buffer\_size và buffer\_interval phù hợp (ví dụ 5 MB hoặc 60s, tùy cái nào đến trước thì gửi).
    *   Định dạng: chọn Direct PUT (không chuyển đổi format) để lưu raw log as-is (hoặc có thể chọn nén gzip).
    *   Prefix trong S3: ví dụ logs/!{timestamp:yyyy/MM/dd}/ để Firehose tự tạo folder theo ngày.
    *   Role IAM cho Firehose: cấp quyền putObject, getBucket, listBucket.
15.  **Trên Local (LocalStack):** Do Firehose chưa hỗ trợ, ta làm khác:
    *   Tạo một **AWS Lambda** (function) gọi là kinesis\_to\_s3\_consumer. Viết code (Python) sử dụng handler Kinesis: hàm này sẽ được LocalStack trigger mỗi khi có batch record trên stream.
    *   Code Lambda: loop qua các record event, parse data (nếu base64 thì decode), sau đó dùng boto3 S3 client (trỏ LocalStack) ghi vào bucket với key gồm timestamp.
    *   Triển khai Lambda bằng Terraform (aws\_lambda\_function với package từ code).
    *   Thiết lập aws\_lambda\_event\_source\_mapping để mapping Kinesis stream -> Lambda (với StartingPosition = LATEST).
    *   Lưu ý: vì LocalStack cho phép Lambda truy cập S3 local mà không cần cred đặc biệt, code có thể dùng endpoint url.
16.  _Sinh dữ liệu thử:_ Triển khai một **Lambda dummy producer** (như đã nói trong Phase 1) hoặc đơn giản dùng AWS CLI put-record:
17.  Ví dụ AWS CLI (LocalStack): awslocal kinesis put-record --stream-name <name> --partition-key test --data '{"service":"TestSvc","message":"hello"}'.
18.  Hoặc chạy Lambda producer (nếu có).
19.  _Kiểm tra kết quả:_
20.  Dùng AWS CLI liệt kê bucket: awslocal s3 ls s3://<bucket-name>/logs/2025/10/29/.
21.  Tải file log về: awslocal s3 cp s3://<bucket>/logs/2025/10/29/15/logs-0001.json ./ (giả sử file tên logs-0001.json).
22.  Mở file, xem có nội dung JSON line tương ứng record đã gửi hay không.

**Tiêu chí hoàn thành tác vụ mẫu:** - Sau khi thực hiện, dữ liệu gửi vào Kinesis (dù bằng tay hay Lambda producer) đã xuất hiện trong file S3 đúng đường dẫn. Mỗi file có thể chứa nhiều record tùy buffer. - Cấu trúc file và tên path khớp với định dạng đề ra (year/month/day). - Không có lỗi trong log Lambda consumer (trên LocalStack có thể xem log qua awslocal or web UI). - Thời gian từ khi put record đến khi file xuất hiện ngắn (vài giây nếu dùng Lambda, vài chục giây nếu do buffer của Firehose).

Ví dụ minh họa trên cho thấy cách tiếp cận tuần tự: cấu hình Terraform trước, sau đó viết mã Lambda cho logic chưa có sẵn dịch vụ, cuối cùng kiểm thử để tin chắc thành phần hoạt động. Các phase khác cũng theo tinh thần tương tự – chia nhỏ tác vụ, làm đâu kiểm tra đó.

## Tiêu chuẩn & Checklist Kết thúc Mỗi Phase

Để đảm bảo chất lượng, cuối mỗi phase, nhóm thực hiện một checklist kiểm tra xem tất cả tiêu chí đã hoàn thành và tuân thủ best practices:

*   **Hoàn thiện IaC:**
*   Chạy terraform validate và terraform fmt không báo lỗi.
*   Terraform plan cho thấy đúng những resource thêm/đổi như dự kiến, không có _drift_ (tài nguyên bị thay đổi ngoài ý muốn).
*   Mọi tài nguyên tạo ra đều được đặt tên đúng convention và có đầy đủ tags.
*   Kiểm tra cross-phase: ví dụ ID của bucket từ Phase 1 được Phase 2 tham chiếu đúng qua output/variable, không hardcode.
*   **Bảo mật:**
*   Kiểm tra IAM: các policy tạo ra có phạm vi hẹp nhất có thể chưa (nếu thấy wildcard "\*", xem có rủi ro không).
*   Secrets (nếu phase có dùng, như Slack webhook) được lưu qua SSM hay Terraform variable nhạy cảm, không in ra log hay output.
*   Kết nối dịch vụ nội bộ (Redis, DB) có bảo vệ (security group, vpc) nếu trên AWS. Nếu local thì các port không mở public trên host trừ khi cần (ví dụ Grafana có thể mở, nhưng Redis/Neo4j nên chỉ trong network Docker).
*   **Giám sát & Logging:**
*   Phase nào thêm Lambda/service thì kiểm tra đã bật log (ví dụ Lambda default log CloudWatch, container có log to console).
*   Các metric quan trọng của phase (như Phase 4: số anomaly, Phase 7: số alert sent) có được thu thập hoặc tính toán chưa, nếu chưa thì tạo kế hoạch bổ sung CloudWatch metric custom.
*   **Tài liệu & Handover:**
*   Cập nhật **README** hoặc tài liệu nội bộ về những gì thực hiện trong phase: cách chạy thử, cách cấu hình. Ví dụ, sau Phase 1, README có mục "Làm thế nào để thêm nguồn log mới" chẳng hạn.
*   Nếu có điểm nào **khác biệt giữa local và AWS** trong phase, ghi chú rõ. Ví dụ: "Local dùng Lambda X thay Firehose Y".
*   **Test & Kết quả mong đợi:**
*   Chạy lại các test unit/integration liên quan phase đó. Đảm bảo tất cả pass.
*   Đối chiếu tiêu chí chấp nhận của phase (đã liệt kê trong tài liệu) với kết quả thực tế. Nếu điểm nào chưa đạt, đánh dấu và lên kế hoạch xử lý trước khi qua phase sau (hoặc quyết định bỏ nếu không trọng yếu và đã chấp nhận trade-off).
*   Lập bảng kết quả nhỏ: ví dụ Phase 4 có thể ghi: "Test 5 tình huống anomaly, phát hiện đúng 4, 1 miss do threshold cao - sẽ điều chỉnh ở phase 8".

Bằng cách tuân thủ checklist này, dự án sẽ hạn chế việc "quên" những bước quan trọng và giữ cho chất lượng đầu ra của mỗi giai đoạn luôn ở mức cao. Việc này cũng giúp khi chuyển giao hệ thống cho nhóm khác hoặc đưa lên môi trường cao hơn, mọi người đều nắm rõ trạng thái của từng phần, tránh bất ngờ.

## Phụ lục: Mapping Tương Ứng Tính năng Local → AWS (Tóm tắt)

Bảng dưới đây tóm tắt cách các thành phần trong môi trường local POC sẽ được thay thế hoặc tương ứng ra sao trên AWS thật:

*   **CloudWatch Logs/Metrics:**
*   _Local:_ Được mô phỏng bằng generator (Lambda giả lập ghi sự kiện) hoặc log có sẵn.
*   _AWS:_ Dùng trực tiếp CloudWatch từ các dịch vụ thật (EC2, Lambda...), có thể chuyển qua Kinesis bằng Subscription.
*   **Kinesis Streams:**
*   _Local:_ Dùng Kinesis của LocalStack (hoặc container Kafka nếu cần).
*   _AWS:_ Dùng Kinesis Data Streams thật (hoặc Amazon MSK nếu công ty chuẩn Kafka).
*   **Kafka (nếu áp dụng):**
*   _Local:_ Chạy container Kafka/Redpanda.
*   _AWS:_ Dùng Amazon Managed Streaming for Kafka (MSK).
*   **S3 Buckets:**
*   _Local:_ LocalStack S3.
*   _AWS:_ Amazon S3 (với đầy đủ tính năng versioning, encryption, lifecycle).
*   **AWS Glue (Crawler, ETL):**
*   _Local:_ Dùng Spark hoặc script cục bộ, Glue Catalog giả lập.
*   _AWS:_ Dùng AWS Glue Crawlers, Glue ETL Jobs, Glue Data Catalog chính thức.
*   **Redis Cache:**
*   _Local:_ Redis Docker container (có module RedisTimeSeries nếu dùng để query chuỗi thời gian).
*   _AWS:_ Amazon ElastiCache for Redis (Cluster mode nếu cần, Multi-AZ để HA).
*   **Time-series DB:**
*   _Local:_ Không có (có thể dùng Redis như trên).
*   _AWS:_ Amazon Timestream, hoặc phương án DIY bằng DynamoDB (bảng với khóa sort theo timestamp).
*   **Athena / SQL Query:**
*   _Local:_ Có thể cài Presto/Trino container nếu muốn giả lập query SQL trên data lake.
*   _AWS:_ Amazon Athena, hoặc Amazon Redshift Spectrum (nếu dùng Redshift).
*   **Phát hiện & Mô hình ML:**
*   _Local:_ Mọi thứ chạy trong Lambda local hoặc container (mô hình ML chạy offline trong code).
*   _AWS:_
    *   Lambda cho phần thống kê và rule.
    *   Amazon SageMaker Endpoint cho mô hình ML (triển khai RCF, CNN tại endpoint, gọi real-time).
    *   Sagemaker cũng có thể dùng để train ban đầu (Phase 8).
*   **Decision Engine:**
*   _Local:_ AWS Step Functions Local (LocalStack) nếu chạy ổn, hoặc thay bằng logic trong Lambda.
*   _AWS:_ AWS Step Functions (chính thức) để orchestration các bước detection, RCA pipeline.
*   **Topology Graph:**
*   _Local:_ Sử dụng Neo4j container và file cấu hình tĩnh.
*   _AWS:_ Dùng AWS X-Ray + có thể bổ sung Neptune (graph DB) để lưu mối quan hệ chi tiết hơn, hoặc tận dụng AWS Service Catalog info.
*   **Bedrock / LLM Service:**
*   _Local:_ "RCA Service" mock (có thể call một mô hình open source nhỏ cài cục bộ, hoặc logic rule-based).
*   _AWS:_ Dùng Amazon Bedrock để truy cập các model LLM mạnh (như AI21, Anthropic) hoặc SageMaker-hosted LLM nếu công ty có model riêng.
*   **Vector DB for knowledge:**
*   _Local:_ OpenSearch container (với k-NN) hoặc Weaviate/Pinecone free dev (nếu cho phép kết nối).
*   _AWS:_ Amazon OpenSearch Serverless (hoặc tự chạy cluster) với tính năng vector, hoặc dịch vụ bên thứ 3 (Pinecone) tùy tích hợp.
*   **Dashboard & Visualization:**
*   _Local:_ Grafana (truy cập data qua Redis, etc.) để xem metric và alert.
*   _AWS:_ Amazon CloudWatch Dashboards, Amazon QuickSight (nếu cần BI), hoặc Grafana Cloud/AWS Managed Grafana.
*   **Alerting Integration:**
*   _Local:_ SQS + Lambda + gọi API Slack/Jira/PagerDuty sandbox.
*   _AWS:_ SQS + Lambda + Secrets (chứa webhook/API keys) + gọi API Slack/Jira/PagerDuty thật (hoặc SNS/SES cho email, Amazon Chime webhook nếu dùng).
*   **Feedback & Training:**
*   _Local:_ Lưu feedback vào S3, train mô hình bằng script local (sklearn/PyTorch container).
*   _AWS:_ Lưu feedback vào S3/Dynamo, dùng AWS Glue/SageMaker để train chính thức. Triển khai mô hình mới qua SageMaker Endpoint (có qui trình A/B testing).
*   **Knowledge Graph:**
*   _Local:_ Neo4j container hoặc tạm trong OpenSearch Graph.
*   _AWS:_ Amazon Neptune (nếu dữ liệu graph phức tạp) hoặc tận dụng OpenSearch nếu scale nhỏ và ít quan hệ phức tạp (OpenSearch có plugin Graph để tìm kết nối trong dữ liệu).

**Kết luận:**

Tài liệu trên đã phác thảo chi tiết kế hoạch xây dựng hệ thống phát hiện bất thường và phân tích nguyên nhân gốc rễ dùng AI, từ giai đoạn POC local đến triển khai thật trên AWS. Các bước được chia pha rõ ràng, kèm nhiệm vụ cụ thể và tiêu chí hoàn thành, giúp đội ngũ thực hiện tuần tự và kiểm soát tốt. Quan trọng hơn, kiến trúc đề xuất sử dụng nhiều best practices hiện đại, đảm bảo hệ thống không chỉ hoạt động được mà còn bền vững, bảo mật, dễ mở rộng về sau.

Khi thực thi dự án, cần linh hoạt điều chỉnh tùy thực tế (đặc biệt về thông số, công cụ phụ), nhưng luôn bám sát mục tiêu cuối cùng: **giảm thời gian phát hiện và xử lý sự cố xuống mức tối thiểu, hỗ trợ tích cực cho đội vận hành thông qua việc tự động hóa thông minh.** Với lộ trình đã vạch ra, hy vọng hệ thống sẽ sớm được hiện thực hóa thành công.