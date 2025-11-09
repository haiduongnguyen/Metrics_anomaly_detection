# Stage 02: ETL - Trích xuất, Chuyển đổi và Tải dữ liệu

## 1. Bối cảnh

Sau khi hoàn thành **Stage 00 (Mock Servers)** để tạo và đẩy dữ liệu log mô phỏng vào Kinesis, và **Stage 01 (Ingestion)** để thiết lập hạ tầng và thu thập dữ liệu thô từ Kinesis vào nơi lưu trữ ban đầu (ví dụ: S3), chúng ta đi đến Stage 02.

Giai đoạn này là trung tâm của việc xử lý dữ liệu. Dữ liệu thô được thu thập ở Stage 01 thường ở nhiều định dạng khác nhau, chưa được chuẩn hóa và không phù hợp để phân tích trực tiếp. Mục tiêu của Stage 02 là lấy dữ liệu thô đó và biến nó thành dữ liệu có cấu trúc, sạch sẽ, và giàu thông tin, sẵn sàng cho các giai đoạn phân tích và phát hiện bất thường sau này.

## 2. Mục tiêu

- **Trích xuất (Extract)**: Đọc dữ liệu log thô đã được thu thập từ Stage 01.
- **Chuyển đổi (Transform)**:
    - **Làm sạch**: Loại bỏ các bản ghi không hợp lệ, xử lý giá trị thiếu.
    - **Chuẩn hóa**: Đưa các định dạng log khác nhau về một cấu trúc chung.
    - **Làm giàu**: Bổ sung thêm thông tin hữu ích (ví dụ: phân giải địa chỉ IP, thêm ngữ cảnh nghiệp vụ).
    - **Tổng hợp**: Tính toán các chỉ số (metrics) quan trọng từ log (ví dụ: số lượng request mỗi phút, tỷ lệ lỗi, độ trễ trung bình).
- **Tải (Load)**: Lưu trữ dữ liệu đã qua xử lý và các chỉ số đã tổng hợp vào một nơi lưu trữ có cấu trúc (ví dụ: Data Lake, Data Warehouse) để phục vụ cho việc truy vấn và phân tích.

## 3. Kiến trúc

Stage 02 bao gồm các thành phần chính sau, được điều phối bởi `docker-compose.yml`:

- **`etl-scheduler`**:
    - **Chức năng**: Dịch vụ này hoạt động như một bộ lập lịch, tự động kích hoạt các công việc ETL theo một chu kỳ định sẵn (ví dụ: mỗi 5 phút).
    - **Công nghệ**: Sử dụng Python với thư viện `APScheduler`.

- **`spark-jobs`**:
    - **Chức năng**: Đây là nơi thực hiện logic ETL cốt lõi, sử dụng sức mạnh của Apache Spark để xử lý dữ liệu lớn.
    - **`logs_processing.py`**: Job Spark chịu trách nhiệm đọc dữ liệu thô, thực hiện các bước làm sạch, chuẩn hóa và làm giàu, sau đó lưu kết quả vào một "khu vực đã xử lý" trong S3 dưới định dạng Parquet tối ưu cho truy vấn.
    - **`metrics_aggregation.py`**: Job Spark đọc dữ liệu đã được xử lý, tính toán các chỉ số tổng hợp (metrics) và lưu chúng vào một nơi riêng biệt để dễ dàng truy cập.

- **`quality-monitor`**:
    - **Chức năng**: Dịch vụ này liên tục chạy các bài kiểm tra chất lượng trên dữ liệu đầu ra của ETL (cả dữ liệu đã xử lý và metrics) để đảm bảo tính toàn vẹn, đầy đủ và chính xác.

- **`dashboard`**:
    - **Chức năng**: Một giao diện web đơn giản để theo dõi trạng thái của các job ETL, xem các chỉ số về chất lượng dữ liệu và có cái nhìn tổng quan về hoạt động của pipeline.

## 4. Luồng hoạt động

1.  **`etl-scheduler`** khởi động và kích hoạt pipeline theo lịch.
2.  Scheduler gọi job **`logs_processing.py`** trên Spark.
3.  Job này đọc dữ liệu thô từ S3, xử lý và ghi dữ liệu sạch vào một bucket/prefix khác trên S3.
4.  Sau khi job xử lý log hoàn tất, scheduler tiếp tục gọi job **`metrics_aggregation.py`**.
5.  Job này đọc dữ liệu sạch, tính toán metrics và lưu kết quả.
6.  Song song đó, **`quality-monitor`** kiểm tra chất lượng dữ liệu đầu ra.
7.  Người dùng có thể truy cập **`dashboard`** để theo dõi toàn bộ quá trình.

## 5. Hướng dẫn sử dụng

### Yêu cầu tiên quyết

- Đảm bảo **Stage 00** và **Stage 01** đang hoạt động. Dữ liệu cần được sinh ra và thu thập liên tục để Stage 02 có đầu vào để xử lý.
- Docker và Docker Compose đã được cài đặt.

### Khởi chạy

Để bắt đầu tất cả các dịch vụ trong Stage 02, chạy lệnh sau từ thư mục `stages/02-etl`:

```bash
docker-compose up --build -d
```

### Kiểm tra

- **Xem log của các dịch vụ**:
  ```bash
  # Theo dõi log của tất cả các container
  docker-compose logs -f

  # Theo dõi log của một dịch vụ cụ thể (ví dụ: scheduler)
  docker-compose logs -f etl-scheduler
  ```
- **Truy cập Dashboard**:
  Mở trình duyệt và truy cập `http://localhost:8052` để xem trang tổng quan của ETL.

### Dừng lại

Để dừng và xóa các container, chạy lệnh:

```bash
docker-compose down
```
