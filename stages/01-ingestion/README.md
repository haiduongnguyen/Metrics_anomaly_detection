# 01-ingestion - Lớp Tiếp nhận Dữ liệu

## Mục tiêu
Tiếp nhận logs và metrics thời gian thực từ các dịch vụ ứng dụng, lưu trữ dữ liệu thô vào hệ thống streaming (Kinesis) và lưu trữ lạnh (S3). Lớp này đóng vai trò cổng vào chính của hệ thống phát hiện bất thường.

## Input
- **Nguồn dữ liệu**: Mock logs/metrics từ các dịch vụ giả lập (OrderService, PaymentService, v.v.)
- **Schema đầu vào**: 
  ```json
  {
    "service": "string",
    "timestamp": "ISO8601",
    "type": "log|metric|apm",
    "metric_name": "string", 
    "value": "number|string",
    "level": "info|warn|error|critical"
  }
  ```
- **Kênh nhận**: Kinesis Streams (local: LocalStack, AWS: Kinesis Data Streams)

## Xử lý
- **Local**: Lambda consumer nhận dữ liệu từ Kinesis, ghi vào S3 raw bucket
- **AWS**: Kinesis Data Firehose tự động ghi vào S3 theo partition thời gian
- **Mock data generator**: Tạo các kịch bản bất thường (spike latency, error burst, deploy regression)
- **Schema validation**: Kiểm tra định dạng dữ liệu đầu vào

## Output
- **S3 path**: `s3://<bucket>/raw/{logs|metrics|apm}/YYYY/MM/DD/HH/*.jsonl`
- **Kinesis stream**: `<project>-<env>-logs-stream`, `<project>-<env>-metrics-stream`
- **Sự kiện**: `ingest.completed` gửi qua EventBridge khi dữ liệu được nhận

## Cách chạy Local
1. Khởi động LocalStack và các dịch vụ phụ trợ:
   ```bash
   docker-compose -f compose/docker-compose.yaml up -d
   ```
2. Triển khai hạ tầng:
   ```bash
   cd infra/stacks/local && terraform init && terraform apply -var-file=../../env/local.tfvars
   ```
3. Chạy mock generator:
   ```bash
   cd services/01-ingestion/generator && python generator.py
   ```

## Chuyển sang AWS
- Thay Kinesis Local bằng Kinesis Data Streams thật
- Sử dụng Kinesis Data Firehose thay vì Lambda consumer
- Cấu hình IAM role phù hợp cho quyền ghi S3
- Bật encryption cho dữ liệu tại rest

## Tiêu chí hoàn thành
- Dữ liệu mock được gửi thành công vào Kinesis
- File dữ liệu thô xuất hiện trong S3 raw bucket theo partition thời gian
- Đảm bảo độ trễ từ lúc gửi đến lúc lưu S3 < vài giây
- Có thể kiểm tra dữ liệu trong LocalStack UI hoặc AWS Console