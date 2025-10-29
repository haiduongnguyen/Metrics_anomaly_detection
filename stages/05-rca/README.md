# 05-rca - Lớp Phân tích Nguyên nhân Gốc rễ

## Mục tiêu
Tự động phân tích nguyên nhân gốc rễ của sự cố bằng cách kết hợp các tín hiệu từ hệ thống với kho tri thức hiện có. Lớp này sử dụng AI (LLM) để suy luận nguyên nhân và đề xuất cách xử lý dựa trên ngữ cảnh sự cố.

## Input
- **Anomaly confirmed**: Từ lớp 04-detection với thông tin chi tiết
- **Topology data**: Đồ thị phụ thuộc dịch vụ (tĩnh trong phiên bản đầu)
- **Log snippets**: Dữ liệu log liên quan quanh thời điểm bất thường
- **Knowledge base**: Tài liệu, runbook, post-mortem từ hệ thống tri thức

## Xử lý
- **Context retrieval**: Thu thập tất cả thông tin liên quan đến sự cố
- **Vector search**: Tìm kiếm tài liệu liên quan trong knowledge base
- **LLM reasoning**: 
  - **Local**: Mock LLM hoặc mô hình nhỏ (GPT-J, Llama)
  - **AWS**: Amazon Bedrock với Claude hoặc Titan
- **Root cause analysis**: Phân tích nguyên nhân khả dĩ dựa trên:
  - Dữ liệu metric bất thường
  - Log lỗi liên quan  
  - Topology ảnh hưởng
  - Tri thức lịch sử
- **Recommendation**: Đề xuất hành động khắc phục

## Output
- **RCA result**: `rca.json` trong S3 path `anomalies-rca/YYYY/MM/DD/`
- **Schema RCA**:
  ```json
  {
    "incident_id": "string",
    "service": "string",
    "root_cause_hypothesis": "string",
    "confidence": "0-1",
    "evidence": ["string"],
    "recommended_actions": ["string"],
    "related_docs": ["doc_url"],
    "blast_radius": ["affected_services"]
  }
  ```
- **Sự kiện**: `anomaly.rca.ready` gửi qua EventBridge

## Cách chạy Local
1. Đảm bảo có anomaly.confirmed events từ lớp 04-detection
2. Khởi động OpenSearch container cho vector search
3. Chạy RCA service:
   ```bash
   cd services/05-rca && python rca_engine.py
   ```
4. Kiểm tra kết quả trong S3 hoặc log

## Chuyển sang AWS
- Sử dụng Amazon Bedrock thay cho mock LLM
- Amazon OpenSearch Serverless cho vector database
- Lambda function cho orchestration
- Kết nối với Confluence/Jira cho knowledge base

## Tiêu chí hoàn thành
- RCA engine trả về kết quả hợp lý với nguyên nhân khả dĩ
- Kết quả bao gồm bằng chứng và đề xuất hành động cụ thể
- Có thể truy cập tài liệu liên quan từ knowledge base
- Thời gian xử lý RCA < vài giây (local), < 1 phút (production)