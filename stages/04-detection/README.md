# 04-detection - Lớp Phát hiện Bất thường

## Mục tiêu
Thực hiện phát hiện bất thường trên dữ liệu metric sử dụng nhiều phương pháp kết hợp: thống kê, rule-based và machine learning. Lớp này tổng hợp kết quả từ các phương pháp khác nhau để xác định sự kiện bất thường với độ tin cậy cao.

## Input
- **Dữ liệu metric**: Window dữ liệu từ Redis (lưu trữ nóng)
- **Tham số cấu hình**: Ngưỡng, trọng số, cửa sổ thời gian từ configs/
- **Schema đầu vào**: Dữ liệu metric theo schema chuẩn từ lớp 02-etl

## Xử lý
- **Phương pháp thống kê**:
  - STL decomposition + IQR trên residual
  - Z-Score / EWMA cho outlier detection
- **Rule-based**: 
  - Ngưỡng cứng (CPU > 90% trong 5 phút)
  - Đạo hàm (spike > 2x so với trung bình)
- **Machine Learning**:
  - Random Cut Forest (RCF) cho anomaly detection
  - Isolation Forest cho unsupervised detection
- **Voting Engine**:
  - ML: 40%, Statistics: 35%, Rule: 25%
  - Yêu cầu ít nhất 2 phương pháp đồng thuận hoặc tổng score > 70%

## Output
- **S3 path**: `s3://<bucket>/anomalies/YYYY/MM/DD/*.json`
- **Schema anomaly**:
  ```json
  {
    "timestamp": "ISO8601",
    "service": "string",
    "metric_name": "string", 
    "value": "number",
    "confidence": "0-1",
    "severity": "low|medium|high|critical",
    "methods_triggered": ["statistical", "ml", "rule"],
    "score_components": {"ml": 0.4, "stat": 0.35, "rule": 0.25}
  }
  ```
- **Sự kiện**: `anomaly.confirmed` gửi qua EventBridge

## Cách chạy Local
1. Đảm bảo có dữ liệu trong Redis từ lớp 03-storage
2. Chạy detection engine:
   ```bash
   cd services/04-detection && python detection_engine.py
   ```
3. Theo dõi log để kiểm tra phát hiện bất thường

## Chuyển sang AWS
- Sử dụng AWS Lambda cho các thuật toán nhẹ
- AWS SageMaker Endpoint cho mô hình ML nặng
- AWS Step Functions cho orchestration workflow
- Cấu hình EventBridge schedule để chạy định kỳ

## Tiêu chí hoàn thành
- Hệ thống phát hiện bất thường trong < 5 giây từ lúc dữ liệu xuất hiện
- Kết quả anomaly bao gồm thông tin từ nhiều phương pháp
- Confidence score hợp lý dựa trên voting
- Không có quá nhiều false positive trong thời gian thử nghiệm