# README.md - Hệ Thống Mô Phỏng Log Bất Thường Ngân Hàng

## 1. Giới Thiệu và Tổng Quan

Hệ thống **Mô Phỏng Log Bất Thường Ngân Hàng** là một môi trường microservices toàn diện, được thiết kế để tạo ra các dòng log thực tế và có chủ đích cho các hệ thống tài chính. Mục tiêu chính là cung cấp dữ liệu chất lượng cao để phát triển, huấn luyện và kiểm thử các hệ thống phát hiện bất thường (Anomaly Detection), giám sát bảo mật (SIEM), và phân tích nghiệp vụ (Business Intelligence).

### Vấn Đề Giải Quyết
- **Thiếu dữ liệu thực tế**: Các hệ thống Anomaly Detection thường thiếu dữ liệu log đa dạng và thực tế để huấn luyện và kiểm thử, đặc biệt là các kịch bản tấn công hoặc lỗi hiếm gặp.
- **Khó tạo kịch bản phức tạp**: Việc giả lập các chuỗi sự kiện bất thường phức tạp, liên quan đến nhiều thành phần hệ thống (infrastructure, application, database) là rất khó khăn.
- **Môi trường thử nghiệm an toàn**: Cung cấp một môi trường cô lập để thử nghiệm các kịch bản rủi ro cao mà không ảnh hưởng đến hệ thống thật.
- **Chuẩn hóa log**: Nhu cầu chuẩn hóa log từ nhiều nguồn khác nhau về một định dạng chung (OpenTelemetry) để dễ dàng xử lý và phân tích.

### Lợi Ích
- **Nâng cao độ chính xác của mô hình AI/ML**: Cung cấp dữ liệu "sạch" và "bất thường" có gán nhãn để huấn luyện các mô hình phát hiện gian lận, tấn công.
- **Giảm thiểu rủi ro**: Phát hiện sớm các lỗ hổng và điểm yếu trong hệ thống giám sát và bảo mật.
- **Tối ưu hóa hiệu năng**: Kiểm thử khả năng chịu tải và phản ứng của hệ thống trước các sự cố đột ngột (CPU spike, memory leak).
- **Tăng tốc độ phát triển**: Rút ngắn thời gian phát triển và triển khai các tính năng liên quan đến bảo mật và giám sát.

## 2. Kiến Trúc Hệ Thống

Hệ thống bao gồm 6 microservices chính, giao tiếp với nhau qua mạng nội bộ của Docker.

```mermaid
graph TD
    subgraph "Giao Diện Người Dùng"
        UI[🌐 Web Browser]
    end

    subgraph "Các Microservices Chính"
        SO[<b>Scenario Orchestrator</b><br/>(Port 8000)<br/>Điều phối kịch bản]
        PG[<b>Pattern Generator</b><br/>(Port 8001)<br/>Tạo mẫu dữ liệu]
        LS[<b>Log Synthesis</b><br/>(Port 8002)<br/>Tổng hợp log chi tiết]
        SM[<b>State Manager</b><br/>(Port 8003)<br/>Quản lý trạng thái]
        II[<b>Ingestion Interface</b><br/>(Port 8004)<br/>Tiếp nhận và lưu trữ log thô]
        LC[<b>Log Consolidation</b><br/>(Port 8005)<br/>Chuẩn hóa và phân tích log]
    end

    subgraph "Luồng Dữ Liệu & Lưu Trữ"
        FS_RAW[(🗂️ File System: Raw Logs<br/>/app/logs/categories)]
        FS_CONSOLIDATED[(📂 File System: Consolidated Logs<br/>/app/logs/consolidated)]
    end

    UI -->|HTTP Request| SO
    UI -->|Xem & Phân tích| LC

    SO -->|Yêu cầu Pattern| PG
    SO -->|Yêu cầu Log| LS
    SO -->|Cập nhật Trạng thái| SM

    LS -->|Gửi Log Thô| II

    II -->|Lưu Log Thô| FS_RAW
    II -->|Forward để chuẩn hóa| LC

    LC -->|Lưu Log Chuẩn Hóa| FS_CONSOLIDATED
```

### Luồng Dữ Liệu Chi Tiết
1.  **Scenario Orchestrator** là bộ não của hệ thống, điều phối các kịch bản. Khi một kịch bản được kích hoạt (tự động hoặc thủ công), nó sẽ:
    *   Yêu cầu **Pattern Generator** tạo ra các chuỗi dữ liệu toán học (ví dụ: hình sin, bước nhảy).
    *   Gửi yêu cầu đến **Log Synthesis** để tạo ra các bản ghi log chi tiết dựa trên các mẫu dữ liệu và loại log cụ thể.
2.  **Log Synthesis** tạo ra 59 loại log khác nhau và chuyển tiếp chúng đến **Ingestion Interface**.
3.  **Ingestion Interface** thực hiện hai nhiệm vụ song song:
    *   **Luồng 1 (Lưu trữ log thô)**: Phân loại và lưu các log thô (raw logs) dưới dạng file JSON lines vào các thư mục tương ứng (`/app/logs/<category>/`). Các log có điểm bất thường cao sẽ được lưu riêng vào thư mục `anomaly`.
    *   **Luồng 2 (Chuẩn hóa)**: Chuyển tiếp ngay lập tức các log thô đến **Log Consolidation** để xử lý.
4.  **Log Consolidation** nhận log thô, chuẩn hóa chúng theo định dạng **OpenTelemetry LogRecord**, và lưu trữ chúng vào một file duy nhất cho mỗi ngày (`/app/logs/consolidated/consolidated_logs_YYYYMMDD.jsonl`). Dịch vụ này cũng cung cấp API để truy vấn và phân tích các log đã được chuẩn hóa.

## 3. Tính Năng Chính của Từng Service

### 1. Scenario Orchestrator (`:8000`)
-   **Điều phối trung tâm**: Quản lý và kích hoạt hơn 200 kịch bản bất thường (90 Technical, 90 Business, 20 Security).
-   **Tạo log liên tục**: Tự động chạy nền để sinh log bình thường và chèn các bất thường ngẫu nhiên với tần suất thực tế (mặc định 1 bất thường/5000 log).
-   **Kích hoạt thủ công**: Giao diện web cho phép người dùng tạo ngay các sự cố phổ biến như CPU Spike, Memory Leak, Database Slow, Network Latency, và các tấn công bảo mật.
-   **Giao diện web trực quan (Tiếng Việt)**: Cung cấp dashboard để theo dõi trạng thái hệ thống, số lượng log, và lịch sử các sự cố đã tạo.

### 2. Pattern Generator (`:8001`)
-   **Mô hình toán học**: Tạo ra các chuỗi dữ liệu theo các mẫu toán học (Gaussian, Step, Sawtooth, Exponential, Poisson) để mô phỏng các xu hướng tăng/giảm của metrics.
-   **Dữ liệu thực tế Việt Nam**: Sinh dữ liệu giả lập tuân thủ các quy tắc của Việt Nam (tên, số điện thoại, địa chỉ IP, số tài khoản ngân hàng).

### 3. Log Synthesis Engine (`:8002`)
-   **Thư viện 59 loại log**: Cung cấp một bộ sưu tập log cực kỳ phong phú, được chia thành 13 danh mục nghiệp vụ, từ log hạ tầng, ứng dụng, bảo mật đến log giao dịch, gian lận, và tuân thủ.
-   **Tự động chuyển tiếp**: Gửi các log đã được tổng hợp đến `Ingestion Interface` để xử lý tiếp.

### 4. State Manager (`:8003`)
-   **Quản lý trạng thái**: Theo dõi trạng thái của các thực thể trong hệ thống (User, Account, Session, System).
-   **Kiểm soát chuyển đổi**: Đảm bảo các thay đổi trạng thái (ví dụ: `active` -> `suspended`) tuân thủ các quy tắc nghiệp vụ đã định.

### 5. Ingestion Interface (`:8004`)
-   **Điểm tiếp nhận log**: Là cổng vào duy nhất cho tất cả các log được sinh ra.
-   **Rate Limiting**: Giới hạn tốc độ ghi log để tránh quá tải hệ thống (mặc định 1000 logs/giây).
-   **Lưu trữ log thô**: Tự động phân loại và lưu log thô vào 13 thư mục khác nhau dựa trên `log_type`.
-   **Tách biệt log bất thường**: Các log có `anomaly_score > 70` được tự động lưu vào thư mục `anomaly/` để dễ dàng phân tích.

### 6. Log Consolidation (`:8005`)
-   **Chuẩn hóa OpenTelemetry**: Chuyển đổi tất cả các định dạng log khác nhau về một cấu trúc **LogRecord** duy nhất, giúp việc truy vấn và phân tích trở nên đồng nhất.
-   **Tối ưu cho RAM thấp (2GB)**:
    *   **File Storage (Mặc định)**: Các log đã chuẩn hóa được ghi thẳng vào file (`/app/logs/consolidated/`), giảm thiểu việc sử dụng RAM.
    *   **RAM Storage (Tùy chọn)**: Có thể bật để phân tích real-time, nhưng yêu cầu nhiều bộ nhớ hơn.
-   **API Phân tích & Thống kê**: Cung cấp các endpoints để lấy thống kê tổng hợp, phân phối theo mức độ nghiêm trọng, và phân tích theo dòng thời gian.

## 4. Hướng Dẫn Cài Đặt và Triển Khai

### Yêu Cầu Hệ Thống
-   **Docker & Docker Compose**: Phiên bản mới nhất.
-   **Hệ điều hành**: Linux, MacOS, hoặc Windows (với WSL2).
-   **RAM**: Tối thiểu **2GB** (với cấu hình mặc định). Khuyến nghị 4GB+ nếu muốn bật RAM storage.
-   **Disk**: Ít nhất 10GB dung lượng trống.

### Các Bước Cài Đặt
1.  **Clone repository**:
    ```bash
    git clone <repository-url>
    cd <repository-name>/stages/00-mock-servers
    ```

2.  **Cấp quyền thực thi cho scripts**:
    ```bash
    chmod +x start.sh stop.sh
    ```

3.  **Khởi động hệ thống**:
    Lệnh này sẽ build các Docker image và khởi chạy tất cả 6 services ở chế độ nền.
    ```bash
    ./start.sh
    ```

4.  **Kiểm tra trạng thái**:
    Sau khoảng 1-2 phút, kiểm tra xem tất cả các services có ở trạng thái `healthy` không.
    ```bash
    docker-compose ps
    ```
    Bạn cũng có thể xem log real-time của tất cả các services:
    ```bash
    docker-compose logs -f
    ```

5.  **Dừng hệ thống**:
    ```bash
    ./stop.sh
    ```

### Cấu hình cho môi trường RAM thấp (2GB)
Hệ thống đã được tối ưu sẵn cho các máy có RAM thấp. Dịch vụ `log-consolidation` mặc định sử dụng chế độ ghi file để tiết kiệm bộ nhớ. Cấu hình này nằm trong file `docker-compose.yml`:
```yaml
# stages/00-mock-servers/docker-compose.yml
services:
  log-consolidation:
    environment:
      - ENABLE_RAM_STORAGE=false    # Mặc định: TẮT
      - ENABLE_FILE_STORAGE=true   # Mặc định: BẬT
      - MAX_RAM_LOGS=1000          # Giới hạn số log trong RAM nếu được bật
```
Bạn không cần thay đổi gì nếu muốn chạy trên máy 2GB RAM.

## 5. Hướng Dẫn Sử Dụng

### Truy Cập Giao Diện Web
-   **Scenario Orchestrator**: `http://localhost:8000` - Giao diện chính để điều khiển và giám sát.
-   **Log Consolidation**: `http://localhost:8005` - Giao diện để xem, lọc, và phân tích các log đã được chuẩn hóa.

### Kích Hoạt Sự Cố Thủ Công
Truy cập `http://localhost:8000`, tìm đến mục "Tạo Sự Cố Bất Thường" và nhấn vào các nút như "🔥 CPU Spike" hoặc "💾 Memory Leak".

Hoặc sử dụng API:
```bash
curl -X POST "http://localhost:8000/api/anomaly/trigger" \
-H "Content-Type: application/json" \
-d '{
    "anomaly_type": "database_slow",
    "intensity": 80,
    "duration_seconds": 90
}'
```

### Xem và Truy Vấn Log

#### Log Thô (Raw Logs)
Log thô được lưu trực tiếp trên máy host của bạn trong thư mục `stages/00-mock-servers/logs/`. Bạn có thể dùng các công cụ dòng lệnh để phân tích:
```bash
# Tìm kiếm các log xác thực thất bại
grep -r "authentication_failure" stages/00-mock-servers/logs/security/

# Đếm số log bất thường về gian lận
jq . stages/00-mock-servers/logs/anomaly/fraud_detection_log_*.log | wc -l
```

#### Log Chuẩn Hóa (Consolidated Logs)
Sử dụng API của dịch vụ `log-consolidation` để truy vấn:
```bash
# Lấy 100 log chuẩn hóa gần nhất
curl "http://localhost:8005/api/consolidated-logs?limit=100" | jq

# Lấy thống kê tổng hợp
curl "http://localhost:8005/api/aggregation/stats" | jq

# Lấy dữ liệu timeline cho 60 phút vừa qua
curl "http://localhost:8005/api/aggregation/timeline?minutes=60" | jq
```
Hoặc truy cập trực tiếp file log đã chuẩn hóa:
```bash
# Đọc file log chuẩn hóa của ngày hôm nay
jq . stages/00-mock-servers/logs/consolidated/consolidated_logs_*.jsonl
```

## 6. Chi Tiết Về Lưu Trữ Log

Hệ thống có **2 luồng lưu trữ log song song** để phục vụ các mục đích khác nhau:

| Đặc điểm | Luồng 1: Log Thô (Raw Logs) | Luồng 2: Log Chuẩn Hóa (Consolidated) |
| :--- | :--- | :--- |
| **Dịch vụ** | `ingestion-interface` | `log-consolidation` |
| **Vị trí** | `logs/<category>/<log_type>_YYYYMMDD.log` | `logs/consolidated/consolidated_logs_YYYYMMDD.jsonl` |
| **Định dạng** | JSON Lines đơn giản, mỗi nguồn một kiểu | **OpenTelemetry LogRecord** (JSON Lines) |
| **Cấu trúc** | Flat, không đồng nhất | Rich, nested, đồng nhất |
| **Tối ưu RAM** | ✅ Rất thấp | ✅ Thấp (chế độ file mặc định) |
| **Mục đích** | Lưu trữ gốc, audit, backup | Phân tích, truy vấn, tích hợp SIEM |

**Ví dụ log thô (`application_log`):**
```json
{"timestamp": "...", "level": "ERROR", "service": "payment-service", "message": "Payment failed", "anomaly_score": 85.0}
```

**Ví dụ log đã chuẩn hóa (cùng log trên):**
```json
{
  "timestamp": "...",
  "body": "[ERROR] payment-service: Payment failed",
  "severity_text": "ERROR",
  "severity_number": 17,
  "attributes": {
    "source": "log-synthesis",
    "original_log_type": "application_log",
    "log.category": "application",
    "level": "ERROR",
    "service": "payment-service",
    "anomaly_score": 85.0
  },
  "resource": {
    "attributes": { "service.name": "log-synthesis-service", ... }
  }
}
```

## 7. Roadmap Phát Triển
- [x] **Tối ưu hóa cho hệ thống 2GB RAM bằng File Storage Mode.**
- [ ] Tích hợp Kafka làm target cho `ingestion-interface`.
- [ ] Bổ sung output connector tới Elasticsearch/Splunk từ `log-consolidation`.
- [ ] Xây dựng các mẫu dashboard Grafana để trực quan hóa metrics.
- [ ] Cung cấp manifest để triển khai trên Kubernetes (K8s).
- [ ] Triển khai cơ chế log rotation và compression tự động.
