# Mô Tả Chi Tiết Kiến Trúc Hệ Thống Phát Hiện Bất Thường và Phân Tích Nguyên Nhân Gốc Rễ

## Tổng Quan Kiến Trúc

Đây là sơ đồ kiến trúc tổng thể end-to-end của hệ thống AI-powered Metrics Anomaly Detection và Root Cause Analysis được xây dựng hoàn toàn trên nền tảng AWS. Kiến trúc được thiết kế theo mô hình phân lớp với luồng dữ liệu chảy từ trái sang phải, từ việc thu thập dữ liệu đến phân tích, cảnh báo và phản hồi.

---

## Phân Tích Chi Tiết Từng Khu Vực

### **Khu Vực 1: Data Sources & Ingestion Layer (Bên Trái)**

**Các Nguồn Dữ Liệu:**

Ở phía trên cùng bên trái, hệ thống thu thập dữ liệu từ ba nguồn chính được biểu diễn bằng các hộp nhỏ:
- **AWS CloudWatch Logs**: Thu thập application logs và system logs
- **AWS CloudWatch Metrics**: Thu thập các chỉ số hệ thống như CPU, memory, disk I/O
- **APM (Application Performance Monitoring)**: Thu thập metrics về performance ứng dụng như latency, throughput, error rate

**Streaming Pipeline:**

Dữ liệu từ các nguồn trên được đưa vào một pipeline streaming được biểu diễn bởi:
- **Amazon Kinesis** (biểu tượng màu xanh dương): Nhận dữ liệu streaming real-time với khả năng xử lý hàng nghìn events/giây
- **Apache Kafka** (biểu tượng màu xanh lá): Làm message broker để đảm bảo data durability và distributed processing

**Initial Storage:**

Các biểu tượng màu hồng/tím ở khu vực này đại diện cho:
- **Amazon S3 Raw Buckets**: Lưu trữ dữ liệu thô chưa xử lý, được phân chia thành:
  - Raw Logs bucket
  - Raw Metrics bucket  
  - Raw APM Metrics bucket

---

### **Khu Vực 2: ETL & Processing Layer (Trung Tâm Trái)**

**AWS Glue Components:**

Khu vực này được đánh dấu bởi các biểu tượng màu xanh lá (AWS Glue):

- **Glue Crawlers**: Tự động scan và catalog dữ liệu từ S3 raw buckets
- **Glue ETL Jobs**: Thực hiện các công việc:
  - Data cleaning: Loại bỏ dữ liệu nhiễu, duplicate
  - Normalization: Chuẩn hóa format, timezone, units
  - Schema transformation: Chuyển đổi sang unified schema
  - Partitioning: Phân vùng dữ liệu theo time và service

**Glue Data Catalog:**

Biểu tượng màu tím đại diện cho Glue Data Catalog - metadata repository trung tâm lưu trữ:
- Table schemas
- Partition information
- Data lineage
- Access permissions

**Transformed Storage:**

Sau ETL, dữ liệu được lưu vào **S3 Transformed Buckets** (biểu tượng màu hồng) với cấu trúc:
- Transformed Logs
- Transformed Metrics
- Transformed APM Data

Dữ liệu này đã sẵn sàng cho analytics và ML inference.

---

### **Khu Vực 3: Hot & Cold Storage Architecture (Trung Tâm)**

**Hot Storage Layer:**

Các biểu tượng màu xanh ngọc (cyan) đại diện cho hot storage components:

- **Amazon ElastiCache / Redis**: Lưu trữ metrics gần đây nhất (last 1-24 hours) với:
  - Sub-millisecond latency
  - TTL (Time To Live) tự động
  - In-memory processing
  - Support cho time-series queries

- **Amazon TimeStream** (có thể): Time-series database tối ưu cho:
  - Real-time metrics queries
  - Automatic data tiering
  - Built-in analytics functions

**Cold Storage:**

- **Amazon S3 (Data Lake)**: Lưu trữ dài hạn với:
  - Lifecycle policies để chuyển sang Glacier
  - Compression để tiết kiệm chi phí
  - Partitioning theo time ranges
  - Support cho big data analytics

**Query Engines:**

Biểu tượng màu tím đại diện cho:
- **Amazon Athena**: SQL queries trực tiếp trên S3 data
- **Amazon Redshift Spectrum**: Analytics queries cho large datasets

---

### **Khu Vực 4: Detection Engine - Multi-Method Approach (Trung Tâm Phải)**

Đây là trái tim của hệ thống, bao gồm ba detection methods chạy song song:

**A. Statistical Detection Layer (Màu xanh lá):**

Ba biểu tượng AWS Lambda đại diện cho các statistical methods:

1. **STL (Seasonal-Trend decomposition using Loess)**:
   - Phân tách time-series thành: Trend + Seasonal + Residual
   - Phát hiện anomalies trong residual component
   - Hiệu quả với dữ liệu có tính mùa vụ

2. **IQR (Interquartile Range)**:
   - Tính Q1 (25th percentile) và Q3 (75th percentile)
   - Anomaly = values outside [Q1-1.5×IQR, Q3+1.5×IQR]
   - Robust với outliers

3. **Z-Score Method**:
   - Tính standard deviation và mean
   - Anomaly = |value - mean| > threshold × std
   - Nhanh và đơn giản

**B. Machine Learning Detection Layer (Màu tím):**

Các biểu tượng Amazon SageMaker endpoints:

1. **Random Cut Forest (RCF)**:
   - Unsupervised anomaly detection
   - Xử lý multi-dimensional data
   - Tính anomaly score từ 0-1
   - Không cần labeled data

2. **SR-CNN (Spectral Residual - Convolutional Neural Network)**:
   - Deep learning approach
   - Học patterns từ historical data
   - Phát hiện complex temporal anomalies
   - Saliency map cho explainability

3. **Clustering Algorithms**:
   - DBSCAN hoặc K-means
   - Nhóm similar anomalies
   - Phát hiện anomaly patterns
   - Correlation analysis

**C. Rule-Based Detection Layer (Màu xanh lá):**

AWS Lambda functions thực thi business rules:
- Threshold-based alerts (CPU > 90%, Memory > 85%)
- Rate of change rules (sudden spike > 50%)
- Duration rules (sustained high for > 5 mins)
- Composite conditions (CPU high AND memory high)

**Decision Engine (Màu tím):**

Biểu tượng Lambda function lớn ở giữa thực hiện:

**Voting Mechanism:**
- Nhận signals từ tất cả detection methods
- Áp dụng weighted voting:
  - ML models: 40% weight
  - Statistical methods: 35% weight
  - Rule-based: 25% weight
- Anomaly confirmed khi ≥2 methods agree
- Tính confidence score: 0-100%

**Anomaly Aggregation:**
- Group anomalies by service, timestamp
- Deduplicate similar alerts
- Rank by severity: Critical > High > Medium > Low

---

### **Khu Vực 5: Service Dependency & Topology (Phía Trên Bên Phải)**

**Service Mesh Visualization:**

Khu vực này được đóng khung màu cam, hiển thị microservices architecture:

**Components:**

Các hộp màu cam đại diện cho các microservices:
- **Gateway Service**: Entry point, API gateway
- **Auth Service**: Authentication & authorization
- **Business Logic Services**: Core application services
- **Database Services**: Data persistence layer

**Connections:**

Các đường kẻ nối giữa services thể hiện:
- Dependencies và data flow
- Request/response patterns
- Service-to-service communications

**AWS App Mesh / X-Ray Integration:**

Biểu tượng màu xanh ngọc (AWS App Mesh) cung cấp:
- Service discovery
- Traffic routing
- Load balancing
- Circuit breaker patterns

**Real-time Topology Visualization:**

Khi anomaly xảy ra, hệ thống:
- Highlight affected service (màu đỏ)
- Show upstream services (màu vàng)
- Show downstream services (màu cam)
- Display blast radius
- Calculate impact scope

**Color Coding:**
- Xanh lá: Healthy services
- Vàng: Warning state
- Cam: Degraded performance
- Đỏ: Critical/Failed

---

### **Khu Vực 6: Root Cause Analysis Engine (Trung Tâm Phải Dưới)**

**AWS Bedrock - AI Reasoning Layer:**

Biểu tượng màu cam lớn (AWS Bedrock) là core của RCA engine:

**Input Signals:**

Bedrock nhận multiple inputs:

1. **Anomaly Scores** (từ Detection Engine):
   - Which metrics are anomalous
   - Severity levels
   - Temporal patterns

2. **Log Snippets** (từ CloudWatch Logs):
   - Error messages
   - Stack traces
   - Warning logs
   - Audit logs

3. **Metrics Time-Series Data**:
   - Historical trends
   - Correlation data
   - Seasonal patterns

4. **Service Dependency Graph**:
   - Topology information
   - Service relationships
   - Communication patterns

5. **Metadata**:
   - Deployment events
   - Configuration changes
   - Business events (Flash Sale, campaigns)

**Knowledge Base Integration:**

Các biểu tượng màu xanh lá và tím đại diện cho:

- **S3 Buckets chứa Runbooks/Playbooks**:
  - Standard Operating Procedures
  - Troubleshooting guides
  - Known issue resolutions
  - Best practices

- **Vector Database** (màu xanh ngọc):
  - Document embeddings
  - Semantic search capability
  - Fast retrieval of relevant docs

- **Confluence Integration** (biểu tượng màu xanh):
  - Architecture documentation
  - Team knowledge base
  - Historical incident reports

**LLM Processing:**

AWS Bedrock sử dụng Large Language Models (Claude hoặc Titan) để:

**Step 1: Context Understanding**
- Parse tất cả input signals
- Identify key entities (services, metrics, errors)
- Extract temporal relationships

**Step 2: Correlation Analysis**
- Tìm correlations giữa metrics
- Identify leading indicators
- Detect cascading failures

**Step 3: Causal Inference**
- Build cause-effect chains
- Rank contributing factors
- Calculate confidence levels

**Step 4: Knowledge Retrieval**
- Query vector database với semantic search
- Retrieve relevant runbooks
- Find similar historical incidents

**Step 5: Reasoning Synthesis**
- Generate root cause hypothesis
- Explain reasoning logic
- Provide evidence supporting conclusion

**Output Generation:**

Bedrock produces structured output:

1. **Root Cause Explanation**:
   - Primary cause với confidence % (e.g., 85%)
   - Contributing factors ranked
   - Timeline of events
   - Natural language summary

2. **Impact Analysis**:
   - Affected services list
   - User impact estimation
   - Business metrics impact

3. **Remediation Recommendations**:
   - Step-by-step action plan
   - Priority levels
   - Estimated time to resolve
   - Rollback procedures nếu cần

4. **Similar Historical Incidents**:
   - Past incidents với similar patterns
   - How they were resolved
   - Lessons learned

---

### **Khu Vực 7: Action & Alerting Layer (Phía Dưới Bên Phải)**

**Alert Manager (Màu tím):**

Component chính điều phối alerts:

**Alert Routing:**

- **Amazon SQS** (biểu tượng màu hồng): Message queue cho alerts
  - Priority queues: Critical, High, Medium, Low
  - Dead letter queue cho failed alerts
  - Batch processing để avoid alert storm

**Alert Enrichment:**

Lambda functions (màu tím) enrich alerts với:
- Root cause analysis từ Bedrock
- Runbook links
- On-call engineer information
- Historical context

**Notification Channels:**

Các biểu tượng ở dưới cùng đại diện cho integration với:

1. **Slack** (biểu tượng màu xanh):
   - Channel-based routing
   - Interactive buttons (Acknowledge, Resolve)
   - Thread conversations
   - Rich formatting với charts

2. **PagerDuty** (có thể):
   - Incident creation
   - Escalation policies
   - On-call scheduling
   - Mobile notifications

3. **Jira** (có thể):
   - Automatic ticket creation
   - Priority mapping
   - Assignment rules
   - Status tracking

4. **Email**:
   - HTML formatted alerts
   - Attachment của charts/logs
   - Distribution lists

**CloudWatch Dashboards:**

Biểu tượng màu tím (CloudWatch) cung cấp:

**Real-time Visualization:**
- Live metrics charts
- Anomaly markers
- Threshold lines
- Historical comparison

**Custom Dashboards:**
- Service health overview
- SLA compliance metrics
- Incident timeline
- Team performance metrics

**Widgets:**
- Line charts cho time-series
- Heat maps cho correlations
- Gauges cho current values
- Logs insights widgets

---

### **Khu Vực 8: Feedback Loop & Continuous Learning (Phía Dưới)**

**Operator Feedback Collection:**

Biểu tượng người dùng (màu xanh) ở góc phải đại diện cho operators:

**Feedback Types:**

1. **Alert Accuracy**:
   - True positive / False positive
   - Severity adjustment
   - Root cause correction

2. **Resolution Details**:
   - Actual actions taken
   - Time to resolve
   - Effectiveness of recommendations

3. **Knowledge Updates**:
   - New troubleshooting steps
   - Updated runbooks
   - Lessons learned

**Feedback Storage:**

Các biểu tượng màu xanh ngọc (S3) lưu:
- Feedback metadata
- Incident reports
- Resolution procedures
- Performance metrics

**Model Retraining Pipeline:**

Biểu tượng màu xanh lá (AWS Glue) và màu tím (SageMaker) thực hiện:

**Step 1: Data Preparation**
- Aggregate feedback data
- Label historical anomalies
- Create training datasets
- Split train/validation/test

**Step 2: Model Retraining**
- Retrain ML models với new data
- Hyperparameter tuning
- Cross-validation
- A/B testing new models

**Step 3: Threshold Adjustment**
- Analyze false positive rates
- Adjust detection thresholds
- Update rule parameters
- Optimize voting weights

**Step 4: Deployment**
- Blue-green deployment
- Canary releases
- Rollback capability
- Performance monitoring

**Knowledge Base Enrichment:**

Lambda functions (màu tím) tự động:
- Update runbooks với new procedures
- Add resolved incidents to knowledge base
- Generate new playbooks
- Improve embeddings quality

**Continuous Improvement Metrics:**

Hệ thống track:
- Detection accuracy over time
- MTTD (Mean Time To Detect) trends
- MTTR (Mean Time To Resolve) trends
- False positive rate reduction
- Operator satisfaction scores

---

### **Khu Vực 9: Batch Processing for Documentation (Trung Tâm Dưới)**

**Confluence Integration:**

Biểu tượng Confluence (màu xanh) ở dưới cùng:

**Scheduled Crawling:**

AWS Glue hoặc Lambda (màu xanh lá) chạy định kỳ:
- Daily crawl của Confluence spaces
- Extract pages, attachments, comments
- Track version changes
- Identify new documentation

**Document Processing Pipeline:**

**Step 1: Content Extraction**
- Parse HTML/Markdown content
- Extract text, images, tables
- Preserve document structure
- Handle attachments

**Step 2: Text Processing**
- Remove boilerplate
- Clean formatting
- Extract key sections
- Identify code blocks

**Step 3: Metadata Enrichment**
- Add timestamps
- Extract authors
- Tag by topic/service
- Link related docs

**Step 4: Embedding Generation**

Sử dụng transformer models (BERT, sentence-transformers):
- Generate 768-dim vectors
- Capture semantic meaning
- Enable similarity search
- Support multi-language

**Step 5: Vector Storage**

Lưu vào vector database (màu xanh ngọc):
- **Pinecone, Weaviate, hoặc OpenSearch**
- Fast similarity search
- Metadata filtering
- Hybrid search (keyword + semantic)

**Knowledge Graph Construction:**

Biểu tượng màu hồng đại diện cho graph database:

**Entities:**
- Services
- Components
- Procedures
- People
- Incidents

**Relationships:**
- Service dependencies
- Procedure applicability
- Expert ownership
- Incident history

**Graph Queries:**
- Find related procedures
- Identify experts
- Trace dependencies
- Discover patterns

---

## Luồng Dữ Liệu End-to-End

### **Luồng Real-time (Màu xanh):**

1. **Data Collection** → CloudWatch thu thập logs/metrics
2. **Streaming Ingestion** → Kinesis/Kafka nhận data streams
3. **Raw Storage** → S3 raw buckets
4. **Stream Processing** → Real-time transformations
5. **Hot Storage** → ElastiCache/TimeStream
6. **Detection** → Statistical + ML + Rule-based (parallel)
7. **Decision** → Voting mechanism confirms anomaly
8. **RCA** → Bedrock analyzes root cause
9. **Alerting** → SQS routes to notification channels
10. **Visualization** → CloudWatch dashboards update

**Latency:** < 5 seconds end-to-end

### **Luồng Batch (Màu cam):**

1. **Scheduled Trigger** → EventBridge triggers Glue jobs
2. **ETL Processing** → Glue transforms raw data
3. **Catalog Update** → Glue Data Catalog updated
4. **Cold Storage** → S3 transformed buckets
5. **Analytics** → Athena queries available
6. **ML Training** → SageMaker retrains models
7. **Knowledge Update** → Documentation processed
8. **Deployment** → New models/rules deployed

**Frequency:** Hourly hoặc daily

### **Luồng Feedback (Màu tím):**

1. **Operator Action** → Feedback submitted via UI
2. **Feedback Storage** → S3 feedback bucket
3. **Aggregation** → Glue jobs aggregate feedback
4. **Analysis** → Identify improvement opportunities
5. **Model Update** → Retrain với labeled data
6. **Threshold Tuning** → Adjust detection parameters
7. **Knowledge Enrichment** → Update runbooks
8. **Validation** → Test improvements
9. **Deployment** → Roll out updates

**Cycle Time:** Weekly hoặc bi-weekly

---

## Các Tính Năng Nổi Bật Của Kiến Trúc

### **1. High Availability & Scalability:**

- Multi-AZ deployment cho tất cả critical components
- Auto-scaling cho Lambda, SageMaker endpoints
- Kinesis sharding tự động
- S3 durability: 99.999999999%

### **2. Security & Compliance:**

- IAM roles với least privilege
- VPC endpoints cho private connectivity
- Encryption at rest (S3, RDS)
- Encryption in transit (TLS/SSL)
- CloudTrail audit logging
- KMS key management

### **3. Cost Optimization:**

- S3 lifecycle policies
- Lambda pay-per-use
- SageMaker inference auto-scaling
- Reserved capacity cho predictable workloads
- Spot instances cho training jobs

### **4. Observability:**

- CloudWatch metrics cho mọi component
- X-Ray distributed tracing
- VPC Flow Logs
- Application logs centralized
- Custom metrics và alarms

### **5. Disaster Recovery:**

- Cross-region S3 replication
- Backup và restore procedures
- Runbook automation
- Chaos engineering testing
- RTO/RPO targets defined

---

## Performance Metrics

### **Detection Performance:**

- **Latency:** < 5 seconds từ event đến alert
- **Throughput:** > 10,000 events/second
- **Accuracy:** > 95% true positive rate
- **False Positive:** < 5%

### **RCA Performance:**

- **Analysis Time:** < 30 seconds
- **Accuracy:** > 85% correct root cause
- **Explainability:** Natural language explanations
- **Actionability:** > 90% recommendations useful

### **System Availability:**

- **Uptime:** 99.9% SLA
- **MTTD:** < 2 minutes
- **MTTR:** < 15 minutes (giảm từ 60+ minutes)
- **Alert Fatigue:** Giảm 70% unnecessary alerts

---

Đây là một kiến trúc enterprise-grade, production-ready với khả năng xử lý hàng triệu events mỗi ngày, cung cấp insights thời gian thực và giúp teams vận hành hệ thống proactively thay vì reactively.