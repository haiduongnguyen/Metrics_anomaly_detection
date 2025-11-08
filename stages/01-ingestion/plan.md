# Kế hoạch Stage 01 – Ingestion (IaC với Terraform trên LocalStack, tương thích AWS)

Mục tiêu của Stage 01 là triển khai lớp Ingestion nhận log/metrics từ Stage 00 (00-mock-servers), đẩy vào streaming storage (Kinesis) và lưu trữ an toàn ở S3 theo chuẩn phân vùng/thư mục để phục vụ các stage kế tiếp (ETL, Detection). Việc triển khai sử dụng IaC bằng Terraform, chạy trước trên LocalStack nhưng giữ 100% khả năng migrate lên AWS thật chỉ bằng thay đổi cấu hình provider.

---

## 1) Phạm vi và mục tiêu

- Nhận dữ liệu từ Stage 00 (đặc biệt consolidated JSONL) và/hoặc các producers nội bộ → Kinesis Streams (real-time) → tiêu thụ và ghi về S3 (raw buckets) theo chuẩn thời gian và service.
- Đảm bảo thiết kế IaC sạch, module hóa, chạy được trên LocalStack; khi lên AWS đổi provider mà không đổi logic.
- Thiết lập các chiến lược xử lý lỗi, quan sát cơ bản, và khả năng scale tuyến tính theo throughput.

Kết quả mong đợi: sau khi `docker compose up` ở thư mục `stages`, toàn bộ pipeline Stage 00 → Stage 01 hoạt động: log được push vào Kinesis (LocalStack) và được lưu về S3 (LocalStack) đúng cấu trúc.

---

## 2) Thành phần kiến trúc chính (bám sát architecture.md)

- Producers (Stage 00):
  - 03-log-synthesis tạo nhiều loại log; 06-log-consolidation hợp nhất thành JSONL; 05-ingestion-interface sẽ gửi record lên Kinesis.
- Streaming Storage:
  - Amazon Kinesis Data Streams (LocalStack): `stage01-logs-stream`, `stage01-metrics-stream` (metrics có thể kích hoạt sau; trước mắt ưu tiên logs).
- Consumer/Delivery (Local-first):
  - Lambda consumer (LocalStack) đọc từ Kinesis, ghi S3 raw theo partition time-based. Lưu ý: Trên AWS thật có thể chuyển sang Firehose → S3; với LocalStack (community) dùng Lambda để tương thích tối đa.
- Raw Storage (Data Lake lớp thô):
  - S3 buckets: `md-raw-logs`, `md-raw-metrics`, (tùy chọn) `md-raw-apm`. Trên AWS sẽ bật versioning, SSE; trên LocalStack bật cấu trúc thư mục chuẩn.
- Quan sát cơ bản:
  - CloudWatch Logs group cho Lambda; CloudWatch metrics/alarms (khi chạy AWS thật). Trên LocalStack mức độ hỗ trợ hạn chế nhưng vẫn giữ cấu hình Terraform sẵn.

---

## 3) Luồng dữ liệu end-to-end (Stage 00 → 01)

1. Stage 00 tạo log và consolidated JSONL.
2. 05-ingestion-interface đọc từng dòng JSONL → gọi `PutRecord(s)` Kinesis (boto3) tới LocalStack (`endpoint_url=http://localstack:4566`).
3. Lambda consumer (event source mapping từ Kinesis) nhận record, buffer/flush theo batch → ghi S3 `md-raw-logs` theo cấu trúc:
   - `s3://md-raw-logs/service=<svc>/year=YYYY/month=MM/day=DD/hour=HH/part-<uuid>.jsonl`
4. (Tùy chọn) Metrics/APM theo luồng tương tự nếu đã sẵn có producer.

---

## 4) Thiết kế IaC bằng Terraform

### 4.1 Cấu trúc thư mục đề xuất

```
stages/01-ingestion/infra
├── main.tf                # Gọi các module và định nghĩa backend
├── providers.tf           # Cấu hình provider localstack và alias aws
├── variables.tf           # Biến chung (region, names, tags, retention,...)
├── outputs.tf
├── env/
│   ├── localstack.tfvars  # Endpoint LocalStack, tên tài nguyên bản local
│   └── aws-dev.tfvars     # Biến khi deploy AWS thật (dev)
└── modules/
    ├── s3_raw/
    │   └── ...            # Buckets: md-raw-logs, md-raw-metrics, md-raw-apm
    ├── kinesis/
    │   └── ...            # Streams + retention, shard count, tags
    ├── iam/
    │   └── ...            # Roles/Policies: Lambda, Kinesis access, S3 write
    └── lambda_consumer/
        └── ...            # Lambda + Event Source Mapping (Kinesis → Lambda)
```

### 4.2 Provider cấu hình

- LocalStack (mặc định khi làm việc local):
  - `provider "aws" { region = "us-east-1"; access_key/secret_key dummy; endpoints = { s3, kinesis, lambda, iam, cloudwatch = "http://localstack:4566" } }`
  - Backend `local` hoặc `s3` trỏ LocalStack để mô phỏng remote state.
- AWS thật (khi migrate):
  - Dùng cùng `provider "aws"` nhưng bỏ `endpoints`, dùng profile/role; giữ nguyên modules và biến.

### 4.3 Tài nguyên cần tạo

- S3 Raw Buckets:
  - `md-raw-logs`, `md-raw-metrics`, `md-raw-apm`
  - Quy ước thư mục: `service=<svc>/year=YYYY/month=MM/day=DD/hour=HH/` (tương thích Athena/Glue về sau).
- Kinesis Data Streams:
  - `stage01-logs-stream` (shard=1 lúc đầu; autoscale bằng tăng shard về sau)
  - `stage01-metrics-stream` (tạo sẵn nhưng có thể tắt producer giai đoạn đầu)
- IAM:
  - Role cho Lambda consumer (policy: `kinesis:Describe/Get/Subscribe`, `s3:PutObject`, `logs:CreateLogGroup/LogStream/PutLogEvents`).
- Lambda consumer:
  - Runtime: Python 3.11 (hoặc NodeJS), memory 256–512MB, timeout 30–60s.
  - Env vars: `TARGET_BUCKET=md-raw-logs`, `PARTITION_BY=time,service`, `FLUSH_MAX_RECORDS`, `FLUSH_INTERVAL_MS`.
  - Event Source Mapping: stream `stage01-logs-stream`, batch size 100–500.
- (Tuỳ chọn) SQS DLQ:
  - `stage01-dlq` để giữ sự kiện lỗi không thể xử lý; Lambda gửi message lỗi vào đây.

### 4.4 Biến môi trường tiêu chuẩn

- Cho producers (05-ingestion-interface):
  - `AWS_ENDPOINT_URL=http://localstack:4566`
  - `AWS_ACCESS_KEY_ID=test`, `AWS_SECRET_ACCESS_KEY=test`, `AWS_DEFAULT_REGION=us-east-1`
  - `KINESIS_STREAM_NAME=stage01-logs-stream`
- Cho Lambda consumer:
  - `TARGET_BUCKET=md-raw-logs`, `OUTPUT_FORMAT=jsonl`, `MAX_BATCH_BYTES=5MB`.

---

## 5) Tích hợp với Stage 00

- 05-ingestion-interface: đảm bảo sử dụng boto3 với `endpoint_url` LocalStack; gửi từng dòng JSONL (UTF-8) vào `PutRecords` (partition key: ví dụ `<service>` hoặc `<service>#<yyyy-mm-dd-hh>` để phân phối shard tốt hơn).
- Docker Compose (tổng thể ở thư mục `stages`):
  - Thêm service `localstack` (nếu chưa có) và network chung cho các container stage 00.
  - Tiêm biến môi trường ở trên vào container `05-ingestion-interface`.
- Định dạng record:
  - JSON phẳng hoặc semi-structured, tối thiểu: `timestamp`, `service`, `level`, `message`, `trace_id` (nếu có), `source`.

---

## 6) Xử lý lỗi và độ tin cậy

- Lambda retry theo mặc định; cấu hình `maximum_retry_attempts`/`bisect_batch_on_function_error` để cô lập record lỗi.
- DLQ SQS cho record không xử lý được; log chi tiết vào CloudWatch Logs (LocalStack vẫn giữ cấu hình).
- Idempotency: sử dụng `record_id` làm khóa khi cần tránh ghi trùng; hoặc ghi kèm `ingest_id`/`uuid` để truy vết.
- Backpressure: điều chỉnh `batch_size`, `parallelization_factor` của event source mapping; tăng shard Kinesis khi throughput cao.

---

## 7) Khả năng mở rộng và hiệu năng

- Kinesis: scale bằng shard count; theo dõi `GetRecords.IteratorAgeMilliseconds` (trên AWS thật) để phát hiện trễ.
- Lambda: điều chỉnh memory/concurrency; batching 100–500; nén GZIP trước khi ghi S3 (tùy chọn) để tiết kiệm chi phí.
- S3 layout: partition theo hour; file size mục tiêu 50–200MB để tối ưu truy vấn batch sau này (ETL/Athena/Glue).

---

## 8) Bảo mật và tuân thủ (khi lên AWS thật)

- S3: bật SSE-S3 hoặc SSE-KMS; bucket policy chặt; block public access.
- IAM: nguyên tắc least-privilege; tách role runtime và role deploy.
- VPC endpoints: cho Lambda/Kinesis/S3 nếu triển khai private.
- CloudTrail: audit access; tag tài nguyên đầy đủ.

---

## 9) Tương thích AWS & chiến lược migrate

- Giữ tên tài nguyên, layout S3, biến môi trường y hệt giữa LocalStack và AWS.
- Khi migrate: đổi provider (bỏ endpoints), bật versioning/SSE/KMS/Alarms; cân nhắc thay Lambda consumer bằng Kinesis Data Firehose → S3 để giảm code vận hành.
- Không đổi gì ở producers (Stage 00); chỉ đổi cấu hình endpoint.

---

## 10) Quy trình triển khai & kiểm thử

1. Khởi động LocalStack qua docker compose chung.
2. Terraform:
   - `cd stages/01-ingestion/infra`
   - `terraform init`
   - `terraform plan -var-file=env/localstack.tfvars`
   - `terraform apply -var-file=env/localstack.tfvars`
3. Khởi động Stage 00 (docker compose ở `stages/00-mock-servers` hoặc compose gộp ở `stages`).
4. Xác nhận:
   - Gửi thử vài record test vào Kinesis (awslocal/boto3) → kiểm tra file xuất hiện ở `md-raw-logs/...` đúng partition.
   - Kiểm tra CloudWatch Logs của Lambda (LocalStack) để xem lỗi/batch.
5. Tải/áp lực: tăng tốc độ gửi record từ 05-ingestion-interface, theo dõi trễ tiêu thụ và điều chỉnh batch/shard.

Acceptance Criteria:
- Log từ Stage 00 xuất hiện trong S3 (LocalStack) theo layout đã quy ước, không mất dữ liệu, không duplicate đáng kể.

---

## 11) Rủi ro & phương án thay thế

- Firehose trên LocalStack (community) có thể hạn chế: dùng Lambda consumer thay thế (đã chọn).
- Một số CloudWatch features không đầy đủ trên LocalStack: giữ cấu hình Terraform, chấp nhận quan sát hạn chế khi local.
- Dung lượng file nhỏ lẻ (nhiều object) làm tăng chi phí trên AWS thật: gom batch và nén GZIP để tối ưu.

---

## 12) Lộ trình mở rộng (liên kết các stage sau)

- Stage 02 (ETL): Glue Crawlers + Jobs đọc từ `md-raw-logs`/`md-raw-metrics` → `md-transformed-*`, đăng ký Glue Data Catalog.
- Stage 03/04 (Storage/Detection): Tích hợp TimeStream/Redis (hot), Athena/Redshift Spectrum (cold), Decision Engine.
- Stage 06 (Alerting): route alerts vào SQS/Slack/Jira sau phát hiện bất thường.

---

## 13) Phụ lục: Schema record log đề xuất (tham khảo)

```json
{
  "timestamp": "2025-01-25T10:45:12.345Z",
  "service": "api-gateway",
  "level": "ERROR",
  "message": "Timeout calling user-service",
  "trace_id": "abc123",
  "source": "mock",
  "extra": {"latency_ms": 1200, "http_status": 504}
}
```

Ghi chú: giữ JSONL (mỗi dòng 1 JSON), UTC ISO-8601; partition bởi `year/month/day/hour` và thư mục `service=<svc>`.
