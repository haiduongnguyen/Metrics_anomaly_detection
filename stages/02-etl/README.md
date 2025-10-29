# 02-etl - Lớp Xử lý & Chuyển đổi Dữ liệu

## Mục tiêu
Xử lý dữ liệu thô từ lớp ingestion, chuẩn hóa schema, làm sạch và chuẩn bị dữ liệu cho hệ thống phân tích. Lớp này chuyển đổi dữ liệu thô thành định dạng chuẩn, sẵn sàng cho các bước phát hiện bất thường.

## Input
- **Nguồn dữ liệu**: S3 raw bucket với partition theo ngày/giờ
- **Định dạng**: JSON Lines (.jsonl) từ lớp 01-ingestion
- **Schema đầu vào**: Dữ liệu chưa chuẩn hóa từ các nguồn khác nhau

## Xử lý
- **Local**: Spark job (có thể dùng container) hoặc script Python xử lý batch
- **AWS**: AWS Glue ETL Jobs với PySpark scripts
- **Chuẩn hóa schema**: 
  - Đồng bộ định dạng timestamp (UTC)
  - Chuyển đổi đơn vị đo lường
  - Thêm trường chuẩn (environment, service_group, v.v.)
- **Làm sạch dữ liệu**: Lọc bỏ bản ghi lỗi, chuẩn hóa định dạng
- **Glue Crawler**: Quét S3 transformed để tạo metadata catalog (chỉ AWS)

## Output
- **S3 path**: `s3://<bucket>/transformed/date=YYYY-MM-DD/service=<name>/*.parquet`
- **Schema chuẩn hóa**: 
  ```json
  {
    "timestamp": "ISO8601 UTC",
    "service_id": "string",
    "metric_name": "string", 
    "value": "number",
    "unit": "string",
    "environment": "dev|staging|prod"
  }
  ```
- **Glue Catalog**: Database và tables cho dữ liệu transformed (chỉ AWS)

## Cách chạy Local
1. Đảm bảo dữ liệu raw đã có trong S3 LocalStack
2. Chạy Spark job xử lý batch:
   ```bash
   cd services/02-etl && python etl_job.py --input s3://raw-bucket --output s3://transformed-bucket
   ```
3. Kiểm tra output trong transformed bucket

## Chuyển sang AWS
- Chuyển Spark job thành AWS Glue ETL Job
- Sử dụng Glue Data Catalog để quản lý schema
- Cấu hình IAM role cho Glue với quyền đọc/ghi S3 và cập nhật catalog
- Thiết lập schedule cho Glue Job (mỗi giờ hoặc mỗi ngày)

## Tiêu chí hoàn thành
- Dữ liệu transformed được ghi vào S3 theo partition chuẩn
- Schema dữ liệu tuân thủ định dạng chuẩn hóa
- (AWS) Glue Data Catalog được cập nhật thành công
- Có thể truy vấn dữ liệu qua Athena (AWS) hoặc hệ thống query khác