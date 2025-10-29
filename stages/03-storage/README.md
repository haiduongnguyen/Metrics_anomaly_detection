# 03-storage - Lớp Lưu trữ (Nóng & Lạnh)

## Mục tiêu
Quản lý kiến trúc lưu trữ hai tầng: lưu trữ nóng (hot storage) cho truy vấn thời gian thực và lưu trữ lạnh (cold storage) cho dữ liệu lịch sử. Đảm bảo dữ liệu được truy cập nhanh chóng cho các thuật toán phát hiện bất thường trong khi vẫn duy trì lịch sử dài hạn.

## Input
- **Dữ liệu thời gian thực**: Từ dòng sự kiện của lớp 01-ingestion
- **Dữ liệu lịch sử**: Từ lớp 02-etl đã được xử lý

## Xử lý
- **Lưu trữ nóng (Hot storage)**:
  - Redis (ElastiCache) cho cache metric gần thời gian thực
  - Key schema: `metrics:{service}:{metric_name}`
  - TTL: 24 giờ cho dữ liệu gần nhất
- **Lưu trữ lạnh (Cold storage)**:
  - Amazon S3 với lifecycle policy
  - Partition theo ngày/tháng cho truy vấn hiệu quả
  - Chuyển sang Glacier sau X ngày (chỉ AWS)

## Output
- **Redis**: Dữ liệu metric mới nhất có thể truy vấn trong < vài chục ms
- **S3 cold storage**: Dữ liệu lịch sử đầy đủ với partition theo thời gian
- **Sự kiện**: `storage.hot.updated` và `storage.cold.archived` cho hệ thống biết dữ liệu đã sẵn sàng

## Cách chạy Local
1. Khởi động Redis container (đã bao gồm trong docker-compose)
2. Chạy service cập nhật Redis từ dữ liệu stream:
   ```bash
   cd services/03-storage && python redis_adapter.py
   ```
3. Kiểm tra dữ liệu trong Redis:
   ```bash
   docker exec -it redis-container redis-cli
   KEYS metrics:*
   ```

## Chuyển sang AWS
- Thay Redis container bằng Amazon ElastiCache Redis cluster
- Cấu hình Multi-AZ cho độ sẵn sàng cao
- Thiết lập VPC và security groups phù hợp
- Tùy chọn: Amazon Timestream cho dữ liệu time-series chuyên dụng

## Tiêu chí hoàn thành
- Dữ liệu metric mới được cập nhật vào Redis trong < 1-2 giây
- Có thể truy vấn dữ liệu gần thời gian thực từ Redis
- Dữ liệu lịch sử được lưu trữ trên S3 theo đúng partition
- (AWS) ElastiCache cluster hoạt động ổn định với Multi-AZ