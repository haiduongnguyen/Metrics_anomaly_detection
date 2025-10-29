# 06-alerting - Lớp Cảnh báo & Hành động

## Mục tiêu
Quản lý việc gửi cảnh báo sự cố đến các kênh phù hợp với thông tin được enrich từ phân tích nguyên nhân gốc rễ. Lớp này cũng xử lý phản hồi từ người vận hành và cung cấp cơ chế tương tác hai chiều.

## Input
- **RCA completed**: Từ lớp 05-rca với phân tích chi tiết
- **Anomaly data**: Thông tin sự cố từ lớp 04-detection
- **Routing config**: Cấu hình định tuyến theo severity, service, thời gian
- **On-call schedule**: Danh sách người phụ trách theo dịch vụ

## Xử lý
- **Alert enrichment**:
  - Kết hợp thông tin anomaly và RCA
  - Thêm link runbook, tài liệu liên quan
  - Xác định người on-call phù hợp
- **Routing engine**:
  - Critical: PagerDuty + Slack #critical-alerts
  - High: Slack #alerts + Jira ticket
  - Medium: Slack #notifications
  - Low: Log only
- **Channel integration**:
  - **Slack**: Webhook với interactive buttons
  - **PagerDuty**: Events API cho incident creation
  - **Jira**: REST API cho ticket creation
  - **Email**: SES hoặc SMTP integration
- **SQS queuing**: Buffer alert với retry và DLQ

## Output
- **Slack message**: Rich message với severity, RCA, runbook, ack buttons
- **PagerDuty**: Incident được tạo tự động
- **Jira ticket**: Issue với tiêu đề, mô tả, liên kết RCA
- **Sự kiện phản hồi**: `alert.acknowledged`, `alert.resolved`

## Cách chạy Local
1. Đảm bảo có anomaly.rca.ready events từ lớp 05-rca
2. Cấu hình biến môi trường với webhook URLs (sandbox)
3. Chạy alert manager:
   ```bash
   cd services/06-alerting && python alert_manager.py
   ```
4. Kiểm tra các kênh để xác nhận nhận alert

## Chuyển sang AWS
- Sử dụng SQS queues với DLQ cho độ tin cậy
- AWS Lambda cho alert processing
- Secrets Manager cho API keys và webhook URLs
- SNS cho email notifications nếu cần

## Tiêu chí hoàn thành
- Alert được gửi đến đúng kênh trong < 5 giây sau RCA
- Nội dung alert bao gồm thông tin RCA, severity, runbook
- Người dùng có thể acknowledge/resolution qua Slack
- Không có duplicate alerts hoặc alert storms
- DLQ không có messages (không lỗi gửi alert nghiêm trọng)