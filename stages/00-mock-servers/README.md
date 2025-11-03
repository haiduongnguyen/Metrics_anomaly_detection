# Hệ Thống Mô Phỏng Log Bất Thường Ngân Hàng

Hệ thống microservices tự động tạo **59 loại log toàn diện** với khả năng mô phỏng **20 kịch bản sự cố hạ tầng** thực tế, phục vụ cho việc kiểm thử và huấn luyện các hệ thống phát hiện bất thường.

## 🎯 Hệ Thống Làm Gì?

Hệ thống này mô phỏng một hệ thống ngân hàng thật đang hoạt động với khả năng:

- ✅ **Tạo log liên tục tự động** (mặc định: 100 log/giây)
- ✅ **Tự động chèn bất thường** với tần suất thấp (mặc định: 1/5,000 log = 0.02%)
- ✅ **Ghi log vào file** theo 12 danh mục chuyên biệt
- ✅ **Hỗ trợ 59 loại log** từ Infrastructure đến Business Intelligence
- ✅ **UI trực quan** để tạo sự cố thủ công
- ✅ **20 kịch bản sự cố** hạ tầng được định nghĩa sẵn
- ✅ **Chạy 24/7** không cần can thiệp

## 🎨 Giao Diện Tạo Sự Cố Thủ Công

Hệ thống cung cấp giao diện web trực quan tại **http://localhost:8000** để bạn có thể:

### Tính Năng UI

1. **8 Nút Preset Sự Cố Nhanh:**
   - 🔥 CPU Spike (Tăng đột biến CPU)
   - 💾 Memory Leak (Rò rỉ bộ nhớ)
   - 🌐 Network Latency (Trễ mạng)
   - 💿 Disk I/O Issue (Vấn đề đọc/ghi đĩa)
   - 🔒 Security Breach (Vi phạm bảo mật)
   - 💳 Payment Failure (Lỗi thanh toán)
   - 🗄️ Database Slow (Database chậm)
   - 🔗 API Timeout (API timeout)

2. **Form Tùy Chỉnh Chi Tiết:**
   - Chọn loại log cụ thể (59 loại)
   - Điều chỉnh mức độ nghiêm trọng (0-100)
   - Thiết lập thời gian kéo dài (giây)
   - Số lượng log tạo ra

3. **Thống Kê Real-time:**
   - Tổng số log đã tạo
   - Số lượng anomaly
   - Tỷ lệ anomaly
   - Thời gian chạy

### Cách Sử Dụng UI

\`\`\`bash
# 1. Mở trình duyệt và truy cập
http://localhost:8000

# 2. Nhấn một trong 8 nút preset để tạo sự cố nhanh
# Hoặc

# 3. Điền form tùy chỉnh:
#    - Log Type: Chọn từ dropdown (59 loại)
#    - Severity: 0-100 (càng cao càng nghiêm trọng)
#    - Duration: Thời gian kéo dài (giây)
#    - Count: Số lượng log

# 4. Nhấn "Trigger Custom Anomaly"

# 5. Xem log được tạo real-time trong thư mục logs/
\`\`\`

## 📋 59 Loại Log Được Hỗ Trợ

### I. Infrastructure & System Logs (9 loại)

1. **server_log** - Log máy chủ (CPU, RAM, Disk)
2. **container_log** - Log Docker/Kubernetes containers
3. **network_log** - Log mạng (latency, packet loss, bandwidth)
4. **storage_log** - Log lưu trữ (IOPS, throughput, capacity)
5. **cdn_log** - Log CDN (cache hit/miss, response time)
6. **dns_log** - Log DNS queries và responses
7. **load_balancer_log** - Log cân bằng tải
8. **firewall_log** - Log tường lửa (allow/deny rules)
9. **vpn_log** - Log VPN connections

### II. Application Layer Logs (6 loại)

10. **application_log** - Log ứng dụng chung
11. **api_log** - Log API requests/responses
12. **microservice_log** - Log microservices
13. **middleware_log** - Log middleware (message queue, cache)
14. **cache_log** - Log Redis/Memcached
15. **message_queue_log** - Log Kafka/RabbitMQ

### III. Database & Data Store Logs (8 loại)

16. **database_log** - Log database chung
17. **sql_query_log** - Log SQL queries
18. **nosql_log** - Log MongoDB/Cassandra
19. **redis_log** - Log Redis operations
20. **elasticsearch_log** - Log Elasticsearch
21. **database_replication_log** - Log database replication
22. **database_backup_log** - Log backup/restore
23. **slow_query_log** - Log slow queries

### IV. Security & Authentication Logs (7 loại)

24. **security_log** - Log bảo mật chung
25. **authentication_log** - Log đăng nhập/đăng xuất
26. **authorization_log** - Log phân quyền
27. **waf_log** - Log Web Application Firewall
28. **ids_ips_log** - Log Intrusion Detection/Prevention
29. **dlp_log** - Log Data Loss Prevention
30. **encryption_log** - Log mã hóa/giải mã

### V. Business Transaction Logs (5 loại)

31. **transaction_log** - Log giao dịch chung
32. **payment_log** - Log thanh toán
33. **transfer_log** - Log chuyển tiền
34. **settlement_log** - Log đối soát
35. **clearing_log** - Log thanh toán bù trừ

### VI. Fraud Detection & AML Logs (3 loại)

36. **fraud_detection_log** - Log phát hiện gian lận
37. **aml_log** - Log chống rửa tiền (AML)
38. **kyc_log** - Log xác thực khách hàng (KYC)

### VII. User Behavior & Analytics Logs (6 loại)

39. **user_activity_log** - Log hoạt động người dùng
40. **session_log** - Log phiên làm việc
41. **clickstream_log** - Log click chuột
42. **navigation_log** - Log điều hướng
43. **search_log** - Log tìm kiếm
44. **conversion_log** - Log chuyển đổi

### VIII. Compliance & Audit Logs (3 loại)

45. **audit_log** - Log kiểm toán
46. **regulatory_log** - Log tuân thủ quy định
47. **gdpr_log** - Log GDPR compliance

### IX. External Integration Logs (3 loại)

48. **api_gateway_log** - Log API Gateway
49. **webhook_log** - Log webhooks
50. **third_party_log** - Log tích hợp bên thứ 3

### X. Monitoring & Observability Logs (3 loại)

51. **metrics_log** - Log metrics (Prometheus)
52. **trace_log** - Log distributed tracing
53. **alert_notification_log** - Log thông báo cảnh báo

### XI. Business Intelligence & Analytics Logs (2 loại)

54. **analytics_log** - Log phân tích dữ liệu
55. **reporting_log** - Log báo cáo

### XII. Specialized Logs (4 loại)

56. **ml_model_log** - Log machine learning models
57. **blockchain_log** - Log blockchain transactions
58. **risk_scoring_log** - Log đánh giá rủi ro
59. **alert_log** - Log cảnh báo

## 🎭 20 Kịch Bản Sự Cố Hạ Tầng

Hệ thống hỗ trợ 20 kịch bản sự cố infrastructure được định nghĩa chi tiết:

### Nhóm 1: CPU & Memory (5 kịch bản)

1. **CPU_SPIKE** - Tăng đột biến CPU lên 95%+
2. **MEMORY_LEAK** - Rò rỉ bộ nhớ tăng dần
3. **THREAD_EXHAUSTION** - Cạn kiệt thread pool
4. **GC_PRESSURE** - Garbage Collection quá tải
5. **CONTEXT_SWITCHING** - Context switching cao bất thường

### Nhóm 2: Network (5 kịch bản)

6. **NETWORK_LATENCY** - Độ trễ mạng tăng cao
7. **PACKET_LOSS** - Mất gói tin
8. **BANDWIDTH_SATURATION** - Băng thông bão hòa
9. **DNS_RESOLUTION_FAILURE** - Lỗi phân giải DNS
10. **CONNECTION_TIMEOUT** - Timeout kết nối

### Nhóm 3: Storage & I/O (5 kịch bản)

11. **DISK_IO_BOTTLENECK** - Nghẽn cổ chai I/O đĩa
12. **DISK_SPACE_EXHAUSTION** - Hết dung lượng đĩa
13. **INODE_EXHAUSTION** - Hết inode
14. **SLOW_DISK_READ** - Đọc đĩa chậm
15. **RAID_DEGRADATION** - RAID suy giảm

### Nhóm 4: Application & Service (5 kịch bản)

16. **SERVICE_UNAVAILABLE** - Service không khả dụng
17. **API_RATE_LIMIT** - Vượt giới hạn API
18. **DATABASE_CONNECTION_POOL** - Cạn kiệt connection pool
19. **CACHE_MISS_STORM** - Cache miss hàng loạt
20. **DEADLOCK_DETECTION** - Phát hiện deadlock

Mỗi kịch bản bao gồm:
- **Metrics cụ thể**: CPU, memory, latency, error rate...
- **Root causes**: Nguyên nhân gốc rễ
- **Severity levels**: Mức độ nghiêm trọng (Low/Medium/High/Critical)
- **Detection logic**: Logic phát hiện
- **Correlation patterns**: Mẫu tương quan với các metrics khác

## 📁 Log Được Lưu Ở Đâu?

### Vị Trí Lưu Trữ

Tất cả log được ghi vào thư mục:

\`\`\`
stages/00-mock-servers/logs/
\`\`\`

### Cấu Trúc Thư Mục (13 Danh Mục)

\`\`\`
stages/00-mock-servers/
├── logs/                           ← Thư mục chứa tất cả log
│   ├── infrastructure/             ← Log hạ tầng (9 loại)
│   │   ├── server_log_20250102.log
│   │   ├── network_log_20250102.log
│   │   ├── container_log_20250102.log
│   │   └── ...
│   ├── application/                ← Log ứng dụng (6 loại)
│   │   ├── application_log_20250102.log
│   │   ├── api_log_20250102.log
│   │   └── ...
│   ├── database/                   ← Log database (8 loại)
│   │   ├── database_log_20250102.log
│   │   ├── sql_query_log_20250102.log
│   │   └── ...
│   ├── security/                   ← Log bảo mật (7 loại)
│   │   ├── security_log_20250102.log
│   │   ├── authentication_log_20250102.log
│   │   └── ...
│   ├── transaction/                ← Log giao dịch (5 loại)
│   │   ├── transaction_log_20250102.log
│   │   ├── payment_log_20250102.log
│   │   └── ...
│   ├── fraud/                      ← Log phát hiện gian lận (3 loại)
│   │   ├── fraud_detection_log_20250102.log
│   │   ├── aml_log_20250102.log
│   │   └── ...
│   ├── user_behavior/              ← Log hành vi người dùng (6 loại)
│   │   ├── user_activity_log_20250102.log
│   │   ├── session_log_20250102.log
│   │   └── ...
│   ├── compliance/                 ← Log tuân thủ (3 loại)
│   │   ├── audit_log_20250102.log
│   │   └── ...
│   ├── integration/                ← Log tích hợp (3 loại)
│   │   ├── api_gateway_log_20250102.log
│   │   └── ...
│   ├── monitoring/                 ← Log giám sát (3 loại)
│   │   ├── metrics_log_20250102.log
│   │   └── ...
│   ├── business_intelligence/      ← Log BI (2 loại)
│   │   ├── analytics_log_20250102.log
│   │   └── ...
│   ├── specialized/                ← Log chuyên biệt (4 loại)
│   │   ├── ml_model_log_20250102.log
│   │   └── ...
│   └── anomaly/                    ← ⚠️ Log bất thường (anomaly_score > 70)
│       └── anomaly_20250102.log
\`\`\`

### Quy Tắc Phân Loại Log

1. **Log thường** (anomaly_score ≤ 70): Ghi vào thư mục danh mục tương ứng
2. **Log bất thường** (anomaly_score > 70): Ghi vào cả 2 nơi:
   - Thư mục danh mục gốc (ví dụ: `transaction/`)
   - Thư mục `anomaly/` (để dễ phân tích)

### Định Dạng Log

Mỗi dòng trong file log là một JSON object:

\`\`\`json
{
  "timestamp": "2025-01-02T10:30:45.123Z",
  "log_type": "payment_log",
  "data": {
    "transaction_id": "TXN20250102103045789",
    "amount": 5000000,
    "currency": "VND",
    "from_account": "****1234",
    "to_account": "****5678",
    "status": "completed",
    "gateway": "VNPAY",
    "processing_time_ms": 1250,
    "anomaly_score": 15.5
  }
}
\`\`\`

### Xem Log Real-time

\`\`\`bash
# Xem log application đang được tạo
tail -f stages/00-mock-servers/logs/application/application_log_$(date +%Y%m%d).log

# Xem log payment
tail -f stages/00-mock-servers/logs/transaction/payment_log_$(date +%Y%m%d).log

# Xem TẤT CẢ log bất thường
tail -f stages/00-mock-servers/logs/anomaly/anomaly_$(date +%Y%m%d).log

# Đếm số dòng log đã tạo
find stages/00-mock-servers/logs/ -name "*.log" -exec wc -l {} + | tail -1
\`\`\`

## 🚀 Hướng Dẫn Khởi Động

### Bước 1: Yêu Cầu Hệ Thống

- **Docker** và **Docker Compose** (bắt buộc)
- **RAM**: Tối thiểu 4GB khả dụng
- **Ổ cứng**: Tối thiểu 10GB trống

Kiểm tra Docker:

\`\`\`bash
docker --version
docker compose version
\`\`\`

### Bước 2: Khởi Động Hệ Thống

\`\`\`bash
# Di chuyển vào thư mục
cd stages/00-mock-servers

# Khởi động (lần đầu mất 2-3 phút để build)
docker compose up --build

# Hoặc chạy nền
docker compose up -d --build
\`\`\`

### Bước 3: Kiểm Tra Hệ Thống

Mở trình duyệt và truy cập:

- **🎨 Scenario Orchestrator (UI)**: http://localhost:8000
- **Pattern Generator**: http://localhost:8001
- **Log Synthesis**: http://localhost:8002
- **State Manager**: http://localhost:8003
- **Ingestion Interface**: http://localhost:8004

Nếu tất cả đều mở được → ✅ Thành công!

### Bước 4: Kiểm Tra Log Đang Được Tạo

\`\`\`bash
# Kiểm tra thư mục logs
ls -la stages/00-mock-servers/logs/

# Xem log real-time
tail -f stages/00-mock-servers/logs/application/application_log_$(date +%Y%m%d).log
\`\`\`

### Bước 5: Dừng Hệ Thống

\`\`\`bash
# Dừng tất cả
docker compose down

# Dừng và XÓA dữ liệu
docker compose down -v
\`\`\`

## 🏗️ Kiến Trúc Hệ Thống

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│           1. Scenario Orchestrator (Port 8000)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  🎨 Web UI - Tạo Sự Cố Thủ Công                      │   │
│  │  • 8 nút preset sự cố nhanh                          │   │
│  │  • Form tùy chỉnh chi tiết                           │   │
│  │  • Thống kê real-time                                │   │
│  └──────────────────────────────────────────────────────┘   │
│  • Quản lý 20 kịch bản sự cố hạ tầng                        │
│  • Tự động tạo log liên tục khi khởi động                   │
│  • Chèn anomaly với tần suất thấp (0.02%)                   │
│  • Hỗ trợ tất cả 59 loại log                                │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐   ┌──────────────┐
│2. Pattern    │   │4. State      │
│   Generator  │   │   Manager    │
│(Port 8001)   │   │(Port 8003)   │
│• Tạo mẫu     │   │• Quản lý     │
│  dữ liệu VN  │   │  trạng thái  │
│• 59 loại log │   │• Audit trail │
└──────┬───────┘   └──────────────┘
       │
       ▼
┌──────────────────────────────────┐
│3. Log Synthesis (Port 8002)      │
│• Tạo log từ mẫu                  │
│• 100 log/giây (mặc định)         │
│• Phân phối tần suất thực tế:     │
│  - Infrastructure: 40%           │
│  - Application: 25%              │
│  - Database: 15%                 │
│  - Security: 10%                 │
│  - Transaction: 5%               │
│  - Khác: 5%                      │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│5. Ingestion Interface (Port 8004) │
│• Nhận log từ Log Synthesis        │
│• Phân loại vào 13 danh mục        │
│• Ghi vào file theo ngày           │
│• Anomaly (score > 70) → anomaly/  │
│• In progress mỗi 10,000 logs      │
└────────┬───────────────────────────┘
         │
         ▼
    📁 logs/
    ├── infrastructure/
    ├── application/
    ├── database/
    ├── security/
    ├── transaction/
    ├── fraud/
    ├── user_behavior/
    ├── compliance/
    ├── integration/
    ├── monitoring/
    ├── business_intelligence/
    ├── specialized/
    └── anomaly/  ← Log bất thường
\`\`\`

## 📊 API Quan Trọng

### Scenario Orchestrator (Port 8000)

\`\`\`bash
# Xem trạng thái tạo log liên tục
curl http://localhost:8000/api/continuous/status

# Dừng tạo log
curl -X POST http://localhost:8000/api/continuous/stop

# Bắt đầu tạo log với cấu hình tùy chỉnh
curl -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{
    "normal_log_rate": 100,
    "anomaly_frequency": 0.0002
  }'

# Tạo sự cố thủ công qua API
curl -X POST http://localhost:8000/api/anomaly/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "payment_log",
    "severity": 85,
    "duration": 300,
    "count": 1000
  }'
\`\`\`

### Log Synthesis (Port 8002)

\`\`\`bash
# Xem tất cả loại log được hỗ trợ
curl http://localhost:8002/api/log-types

# Tạo log cụ thể
curl -X POST http://localhost:8002/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "fraud_detection_log",
    "scenario_id": "FRAUD_001",
    "count": 100,
    "anomaly_score": 85
  }'

# Xem thống kê
curl http://localhost:8002/api/logs/stats
\`\`\`

### Ingestion Interface (Port 8004)

\`\`\`bash
# Xem thống kê log đã ghi
curl http://localhost:8004/api/logs/stats

# Kết quả mẫu:
{
  "base_directory": "/app/logs",
  "log_categories": {
    "infrastructure": {
      "files": 9,
      "total_lines": 150000,
      "total_size_mb": 45.2
    },
    "anomaly": {
      "files": 1,
      "total_lines": 300,
      "total_size_mb": 0.5
    }
  }
}
\`\`\`

## ⚙️ Cấu Hình Tần Suất

### Tần Suất Mặc Định

\`\`\`json
{
  "normal_log_rate": 100,        // 100 log/giây
  "anomaly_frequency": 0.0002    // 1 anomaly mỗi 5,000 log (0.02%)
}
\`\`\`

### Tần Suất Khuyến Nghị

| Môi Trường | Log/giây | Anomaly Frequency | Ý Nghĩa |
|------------|----------|-------------------|---------|
| **Development** | 10-50 | 0.001 (0.1%) | 1 anomaly/1,000 log |
| **Testing** | 100-200 | 0.0002 (0.02%) | 1 anomaly/5,000 log |
| **Staging** | 500-1000 | 0.0001 (0.01%) | 1 anomaly/10,000 log |
| **Production-like** | 1000+ | 0.00005 (0.005%) | 1 anomaly/20,000 log |

### Thay Đổi Tần Suất

\`\`\`bash
# Tăng tần suất anomaly (testing)
curl -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{
    "normal_log_rate": 100,
    "anomaly_frequency": 0.001
  }'

# Giảm tần suất (production-like)
curl -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{
    "normal_log_rate": 1000,
    "anomaly_frequency": 0.00005
  }'
\`\`\`

## 🔍 Giám Sát Hệ Thống

### Kiểm Tra Services

\`\`\`bash
# Xem tất cả containers
docker compose ps

# Xem log của services
docker compose logs -f

# Xem log của một service
docker compose logs -f log-synthesis

# Kiểm tra health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
\`\`\`

### Xem Thống Kê Log

\`\`\`bash
# Xem dung lượng logs
du -sh stages/00-mock-servers/logs/
du -sh stages/00-mock-servers/logs/*/

# Đếm số dòng log
find stages/00-mock-servers/logs/ -name "*.log" -exec wc -l {} + | tail -1

# Đếm anomaly logs
wc -l stages/00-mock-servers/logs/anomaly/*.log
\`\`\`

## 🛠️ Xử Lý Sự Cố

### Vấn Đề 1: Không Thấy Log Anomaly

**Triệu chứng:** Thư mục `logs/anomaly/` rỗng hoặc không có file

**Nguyên nhân:** 
- Anomaly score của log < 70 (ngưỡng mặc định)
- Tần suất anomaly quá thấp (0.02% = 1/5000 log)

**Giải pháp:**

\`\`\`bash
# Cách 1: Tăng tần suất anomaly
curl -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{"normal_log_rate": 100, "anomaly_frequency": 0.01}'

# Cách 2: Tạo anomaly thủ công qua UI
# Mở http://localhost:8000 và nhấn nút "CPU Spike" hoặc "Security Breach"

# Cách 3: Tạo anomaly qua API
curl -X POST http://localhost:8000/api/anomaly/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "payment_log",
    "severity": 90,
    "duration": 60,
    "count": 100
  }'

# Đợi vài giây và kiểm tra
ls -la stages/00-mock-servers/logs/anomaly/
\`\`\`

### Vấn Đề 2: Chỉ Có 3 Thư Mục Log

**Triệu chứng:** Chỉ thấy `application/`, `security/`, `transaction/`

**Nguyên nhân:** Log synthesis chưa tạo đủ các loại log khác

**Giải pháp:**

\`\`\`bash
# Kiểm tra log synthesis có chạy không
curl http://localhost:8002/health

# Xem loại log đang được tạo
curl http://localhost:8002/api/log-types

# Restart services để áp dụng cấu hình mới
docker compose restart

# Đợi 1-2 phút để hệ thống tạo đủ các loại log
sleep 120
ls -la stages/00-mock-servers/logs/
\`\`\`

### Vấn Đề 3: Port Already Allocated

**Triệu chứng:** `Error: Bind for 0.0.0.0:8001 failed`

**Giải pháp:**

\`\`\`bash
# Tìm process đang chiếm port
lsof -i :8001

# Dừng process (thay <PID>)
kill -9 <PID>

# Hoặc đổi port trong docker-compose.yml
# Sửa "8001:8001" thành "9001:8001"
\`\`\`

### Vấn Đề 4: Services Không Khởi Động

**Giải pháp:**

\`\`\`bash
# Xem log lỗi
docker compose logs

# Rebuild từ đầu
docker compose down -v
docker compose build --no-cache
docker compose up -d

# Kiểm tra lại
docker compose ps
\`\`\`

### Vấn Đề 5: Log Tạo Quá Nhanh

**Giải pháp:**

\`\`\`bash
# Giảm tốc độ
curl -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{"normal_log_rate": 10, "anomaly_frequency": 0.0002}'

# Xóa log cũ
rm -rf stages/00-mock-servers/logs/*/2025*.log
\`\`\`

## 📈 Tăng Hiệu Năng

### Tăng Tốc Độ Tạo Log

\`\`\`bash
# 500 log/giây
curl -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{"normal_log_rate": 500, "anomaly_frequency": 0.0002}'

# 1000 log/giây
curl -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{"normal_log_rate": 1000, "anomaly_frequency": 0.0002}'
\`\`\`

### Scale Services

\`\`\`bash
# Scale log-synthesis
docker compose up -d --scale log-synthesis=3

# Scale pattern-generator
docker compose up -d --scale pattern-generator=5
\`\`\`

## 📚 Ví Dụ Sử Dụng

### Ví Dụ 1: Mô Phỏng Tấn Công DDoS

\`\`\`bash
# Qua UI: Nhấn nút "Security Breach"

# Hoặc qua API:
curl -X POST http://localhost:8000/api/anomaly/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "waf_log",
    "severity": 95,
    "duration": 300,
    "count": 5000
  }'
\`\`\`

### Ví Dụ 2: Mô Phỏng Database Chậm

\`\`\`bash
# Qua UI: Nhấn nút "Database Slow"

# Hoặc qua API:
curl -X POST http://localhost:8000/api/anomaly/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "slow_query_log",
    "severity": 80,
    "duration": 600,
    "count": 1000
  }'
\`\`\`

### Ví Dụ 3: Phân Tích Log Bằng Python

\`\`\`python
import json
from pathlib import Path
from collections import Counter

# Đọc tất cả anomaly logs
anomaly_dir = Path('stages/00-mock-servers/logs/anomaly/')
anomalies = []

for log_file in anomaly_dir.glob('*.log'):
    with open(log_file, 'r') as f:
        anomalies.extend([json.loads(line) for line in f])

# Phân tích theo loại log
log_types = Counter(log['log_type'] for log in anomalies)
print("Phân bố anomaly theo loại:", log_types)

# Phân tích theo mức độ nghiêm trọng
high_severity = [
    log for log in anomalies 
    if log['data'].get('anomaly_score', 0) > 85
]
print(f"Anomaly nghiêm trọng (>85): {len(high_severity)}")

# Tìm top 10 anomaly cao nhất
top_anomalies = sorted(
    anomalies, 
    key=lambda x: x['data'].get('anomaly_score', 0),
    reverse=True
)[:10]

for i, log in enumerate(top_anomalies, 1):
    print(f"{i}. {log['log_type']}: {log['data'].get('anomaly_score')}")
\`\`\`

## 🎓 Câu Hỏi Thường Gặp (FAQ)

### Q1: Làm sao để tạo sự cố thủ công?

**Đáp:** Có 3 cách:

1. **Qua UI** (Dễ nhất): Mở http://localhost:8000 và nhấn một trong 8 nút preset
2. **Qua API**: Gọi endpoint `/api/anomaly/trigger` với JSON config
3. **Qua Form tùy chỉnh**: Điền form trên UI với các tham số chi tiết

### Q2: Tại sao không thấy log anomaly?

**Đáp:** Có 3 lý do:

1. **Tần suất quá thấp**: Mặc định 0.02% = 1 anomaly/5,000 log. Tăng lên bằng cách gọi API hoặc tạo thủ công
2. **Anomaly score < 70**: Chỉ log có score > 70 mới được ghi vào `anomaly/`
3. **Chưa đủ thời gian**: Đợi ít nhất 1-2 phút để hệ thống tạo đủ log

### Q3: Làm sao biết log nào là anomaly?

**Đáp:** Kiểm tra field `anomaly_score` trong JSON:

- **0-30**: Bình thường
- **31-50**: Nghi ngờ nhẹ
- **51-70**: Nghi ngờ cao
- **71-85**: Bất thường
- **86-100**: Bất thường nghiêm trọng

Log có score > 70 sẽ được ghi vào thư mục `anomaly/`

### Q4: Có thể tạo chỉ một loại log không?

**Đáp:** Có! Sử dụng API của Log Synthesis:

\`\`\`bash
curl -X POST http://localhost:8002/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "payment_log",
    "scenario_id": "DEMO",
    "count": 1000,
    "anomaly_score": 20
  }'
\`\`\`

### Q5: Log có dữ liệu Việt Nam không?

**Đáp:** Có! Tất cả log sử dụng:
- Số điện thoại VN (090x, 091x...)
- IP của ISP VN (113.161.x.x, 116.103.x.x...)
- Tên người VN (Nguyễn Văn A, Trần Thị B...)
- Địa chỉ VN (Hà Nội, TP.HCM, Đà Nẵng...)
- Tiền tệ VND

### Q6: Làm sao để xóa log cũ?

**Đáp:**

\`\`\`bash
# Xóa tất cả log
rm -rf stages/00-mock-servers/logs/

# Xóa log của một ngày cụ thể
rm -rf stages/00-mock-servers/logs/*/2025-01-01*.log

# Xóa chỉ anomaly logs
rm -rf stages/00-mock-servers/logs/anomaly/*.log
\`\`\`

## 📄 Giấy Phép

MIT License - Xem file LICENSE để biết chi tiết.

---

**Lưu ý:** Hệ thống này chỉ dùng cho mục đích kiểm thử và huấn luyện. Không sử dụng trong môi trường production thực tế.
