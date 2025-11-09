# Stage 03: Storage - Kiến trúc Lưu trữ Đa Tầng cho Phân tích và ML

## 1. Bối cảnh và Động lực

Sau khi hoàn thành **Stage 02 (ETL)** với việc xử lý, chuẩn hóa và tổng hợp dữ liệu từ logs thô thành dữ liệu có cấu trúc và metrics, chúng ta đến với thách thức quan trọng tiếp theo: làm thế nào để lưu trữ hiệu quả khối lượng dữ liệu khổng lồ này phục vụ cho nhiều mục đích khác nhau?

### Thách thức từ Stage 02

Từ Stage 02, chúng ta có:
- **Processed Logs**: Dữ liệu log đã được chuẩn hóa, làm sạch (format Parquet)
- **Aggregated Metrics**: Các chỉ số tổng hợp theo thời gian (error rates, latencies, throughput)
- **Quality Reports**: Metadata về chất lượng dữ liệu và pipeline health

Những dữ liệu này có đặc điểm:
- **Khối lượng lớn**: Hàng TB dữ liệu mỗi ngày từ hệ thống ngân hàng
- **Tốc độ cao**: Metrics cần được cập nhật gần real-time (< 1 phút)
- **Đa dạng truy vấn**: Từ real-time monitoring đến historical analysis
- **Yêu cầu khác nhau**: Hot data cho alerting, warm data cho investigation, cold data cho compliance

### Vị trí trong Kiến trúc Tổng thể

Stage 03 đóng vai trò là **Data Foundation Layer** - nền tảng dữ liệu cho toàn bộ hệ thống:
- **Upstream**: Nhận dữ liệu đã xử lý từ Stage 02
- **Downstream**: Cung cấp dữ liệu cho:
  - Stage 04: Detection Engine (cần truy cập nhanh metrics)
  - Stage 05: Root Cause Analysis (cần historical context)
  - Stage 06: Alerting (cần real-time data)
  - Stage 07: Feedback Loop (cần lưu trữ lâu dài)

## 2. Mục tiêu Chi tiết

### 2.1. Mục tiêu Kinh doanh
- **Giảm chi phí lưu trữ**: Tối ưu hóa chi phí bằng data tiering
- **Tăng tốc độ phân tích**: Query response time < 1 giây cho hot data
- **Đảm bảo compliance**: Lưu trữ audit logs theo quy định (7 năm)
- **Hỗ trợ ML/AI**: Cung cấp training data cho models

### 2.2. Mục tiêu Kỹ thuật
- **Multi-tier Storage**: Hot → Warm → Cold → Archive
- **Query Optimization**: Indexing, partitioning, caching strategies
- **Data Lifecycle**: Tự động migration dữ liệu theo tuổi
- **High Availability**: Replication và disaster recovery
- **Security**: Encryption at rest và in transit

## 3. Kiến trúc Chi tiết

### 3.1. Storage Tiers Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     HOT TIER (0-24 hours)                    │
│  • Redis/ElastiCache: Real-time metrics (< 100ms latency)   │
│  • TimeStream: Time-series data với auto-aggregation        │
│  • DynamoDB: Alert states và active incidents               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    WARM TIER (1-30 days)                     │
│  • S3 Standard: Processed logs và metrics                   │
│  • Athena: Interactive SQL queries                          │
│  • OpenSearch: Full-text search và log analytics           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    COLD TIER (30-365 days)                   │
│  • S3 Infrequent Access: Historical data                    │
│  • Glue Catalog: Metadata và schema registry               │
│  • Redshift Spectrum: Complex analytical queries           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   ARCHIVE TIER (> 1 year)                    │
│  • S3 Glacier: Compliance và audit requirements            │
│  • Glacier Deep Archive: Long-term retention (7+ years)    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2. Components và Responsibilities

#### A. Cache Layer (Hot Tier)
**Redis Cluster (ElastiCache)**
- **Mục đích**: Ultra-low latency access cho critical metrics
- **Data Types**:
  - Current anomaly scores (TTL: 1 hour)
  - Active alert states (TTL: 24 hours)
  - Service health indicators (TTL: 5 minutes)
  - Rate limiting counters
- **Capacity Planning**: 
  - Memory: 64GB distributed across 4 nodes
  - Throughput: 100K ops/second
  - Replication: Multi-AZ với automatic failover

**Amazon TimeStream**
- **Mục đích**: Native time-series database cho metrics
- **Features**:
  - Automatic data tiering (memory → magnetic)
  - Built-in time-series functions
  - SQL-compatible queries
- **Data Organization**:
  - Measures: CPU, Memory, Latency, Error Rate
  - Dimensions: Service, Environment, Region
  - Retention: 24 hours in memory, 30 days in magnetic

**DynamoDB**
- **Mục đích**: Transactional store cho operational data
- **Tables**:
  - `AlertStates`: Current alert status và acknowledgments
  - `IncidentTracking`: Active incident lifecycle
  - `ConfigurationCache`: Detection thresholds và rules
- **Design Patterns**:
  - Single table design với GSIs
  - On-demand billing cho unpredictable workloads
  - Point-in-time recovery enabled

#### B. Operational Store (Warm Tier)
**S3 Standard Buckets**
- **Structure**:
  ```
  s3://vpbank-metrics-warm/
  ├── processed-logs/
  │   ├── year=2025/month=11/day=09/hour=14/
  │   │   ├── service=auth/*.parquet
  │   │   ├── service=payment/*.parquet
  │   │   └── service=gateway/*.parquet
  │   └── _metadata/
  │       └── partition_stats.json
  ├── aggregated-metrics/
  │   ├── 5min-aggregates/
  │   ├── hourly-aggregates/
  │   └── daily-summaries/
  └── quality-reports/
      └── data-quality-metrics/
  ```
- **Partitioning Strategy**:
  - Time-based: year/month/day/hour
  - Service-based: Cho parallel processing
  - Size optimization: 128MB-1GB per file

**Amazon Athena**
- **Mục đích**: Serverless interactive queries
- **Table Design**:
  - Partitioned tables matching S3 structure
  - Columnar format (Parquet) cho compression
  - Projection để automatic partition discovery
- **Query Patterns**:
  - Time-range queries với partition pruning
  - Service-specific investigations
  - Cross-service correlation analysis

**OpenSearch Domain**
- **Mục đích**: Log search và visualization
- **Index Strategy**:
  - Rolling indices: `logs-2025.11.09`
  - Index templates cho consistent mapping
  - Hot-warm architecture với node types
- **Features**:
  - Full-text search với highlighting
  - Aggregations và analytics
  - Kibana dashboards
  - Anomaly detection (built-in ML)

#### C. Analytics Store (Cold Tier)
**S3 Infrequent Access**
- **Migration Policy**:
  - Automatic transition sau 30 days
  - Lifecycle rules based on object tags
  - Intelligent-Tiering cho access pattern optimization
- **Compression**:
  - Parquet với Snappy compression
  - 70-80% space savings
  - Maintained query performance

**AWS Glue Data Catalog**
- **Mục đích**: Central metadata repository
- **Components**:
  - Database schemas
  - Table definitions
  - Partition information
  - Column statistics
- **Integration**:
  - Athena table discovery
  - Redshift Spectrum external tables
  - SageMaker feature store

**Redshift Spectrum**
- **Mục đích**: Complex analytical queries
- **Use Cases**:
  - Monthly trend analysis
  - Year-over-year comparisons
  - ML feature engineering
  - Business intelligence reports

#### D. Archive Store
**S3 Glacier**
- **Retention**: 1-7 years
- **Retrieval Options**:
  - Expedited: 1-5 minutes (emergency)
  - Standard: 3-5 hours (normal)
  - Bulk: 5-12 hours (batch)
- **Vault Lock**: Compliance mode cho regulatory requirements

**Glacier Deep Archive**
- **Retention**: 7+ years
- **Use Cases**:
  - Regulatory compliance
  - Audit trails
  - Historical incident records
- **Retrieval**: 12-48 hours

### 3.3. Data Flow và Lifecycle Management

#### Ingestion Flow (từ Stage 02)
```
ETL Output → S3 Landing Zone → Data Router
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            Hot Tier Loading                Warm Tier Loading
            (Redis, TimeStream)             (S3, OpenSearch)
```

#### Data Aging Process
```
Hour 0-24:    Redis (hot cache) + S3 Standard
Day 1-30:     S3 Standard + OpenSearch indices
Day 31-365:   S3 IA + Compacted formats
Year 1-7:     Glacier + Archived indices
Year 7+:      Deep Archive
```

#### Query Routing Logic
```
Query Request → Query Router → Analyze Time Range
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              Last 24h          Last 30 days      Historical
                    ↓                 ↓                 ↓
            Redis/TimeStream    Athena/OpenSearch   Redshift
```

### 3.4. Performance Optimization Strategies

#### Caching Strategy
- **L1 Cache**: Redis cho most recent metrics (< 1 hour)
- **L2 Cache**: TimeStream memory tier (< 24 hours)
- **L3 Cache**: S3 Standard với CloudFront (< 30 days)
- **Cache Invalidation**: Event-driven và TTL-based

#### Partitioning và Bucketing
- **Time Partitioning**: year/month/day/hour hierarchy
- **Hash Bucketing**: Service name cho even distribution
- **Z-Order**: Multi-dimensional clustering cho Athena
- **Bloom Filters**: Quick existence checks

#### Compression và Format Optimization
- **Parquet**: Columnar storage với predicate pushdown
- **ORC**: Alternative cho Hive-compatible tools
- **Compression Algorithms**:
  - Snappy: Balance giữa speed và ratio
  - ZSTD: Maximum compression cho archive
  - LZ4: Ultra-fast cho hot data

### 3.5. Data Governance và Security

#### Access Control
- **IAM Policies**: Fine-grained permissions per tier
- **S3 Bucket Policies**: Cross-account access rules
- **VPC Endpoints**: Private connectivity
- **Resource Tags**: Cost allocation và access management

#### Encryption
- **At Rest**:
  - S3: SSE-S3 hoặc SSE-KMS
  - Redis: Encryption enabled
  - DynamoDB: Default encryption
- **In Transit**:
  - TLS 1.2+ cho all connections
  - VPN hoặc Direct Connect cho on-premise

#### Audit và Compliance
- **CloudTrail**: API call logging
- **S3 Access Logs**: Object-level access tracking
- **Macie**: Sensitive data discovery
- **Config Rules**: Compliance validation

## 4. Integration Points

### 4.1. Upstream Integration (từ Stage 02)

**ETL Output Handling**
- **Landing Zone**: S3 bucket cho ETL output
- **Event Notifications**: S3 events trigger processing
- **Data Validation**: Schema validation trước khi load
- **Error Handling**: Dead letter queues cho failed records

### 4.2. Downstream Integration

**Stage 04 - Detection Engine**
- **API Gateway**: RESTful endpoints cho metric queries
- **GraphQL**: Flexible data fetching
- **WebSocket**: Real-time metric streaming
- **SDK**: Python/Java clients cho direct access

**Stage 05 - Root Cause Analysis**
- **Historical Context API**: Time-series data retrieval
- **Correlation Service**: Cross-metric analysis
- **Pattern Database**: Known issue patterns

**Stage 06 - Alerting**
- **Alert State Store**: DynamoDB cho alert lifecycle
- **Metric Streaming**: Kinesis Data Streams
- **Notification Queue**: SQS cho alert distribution

## 5. Monitoring và Operations

### 5.1. Key Performance Indicators (KPIs)

**Latency Metrics**
- P50/P95/P99 query latency per tier
- Cache hit rates
- Data freshness (lag từ ingestion)

**Throughput Metrics**
- Queries per second
- Data ingestion rate (GB/hour)
- Concurrent users

**Cost Metrics**
- Storage cost per tier
- Query cost (Athena, Redshift)
- Data transfer costs

### 5.2. Health Checks

**Automated Monitoring**
- CloudWatch alarms cho all services
- Custom metrics via CloudWatch Agent
- Synthetic monitoring cho API endpoints

**Data Quality Checks**
- Completeness: Missing data detection
- Consistency: Cross-tier validation
- Timeliness: Data age monitoring

## 6. Disaster Recovery và High Availability

### 6.1. Backup Strategy
- **Continuous**: DynamoDB point-in-time recovery
- **Daily**: S3 cross-region replication
- **Weekly**: Full metadata backup

### 6.2. Failover Procedures
- **Redis**: Automatic failover với ElastiCache
- **S3**: Multi-region với eventual consistency
- **Database**: Read replicas và standby instances

### 6.3. Recovery Objectives
- **RTO (Recovery Time Objective)**: < 1 hour
- **RPO (Recovery Point Objective)**: < 5 minutes cho hot data

## 7. Capacity Planning

### 7.1. Growth Projections
- **Year 1**: 100TB total storage
- **Year 2**: 300TB với 70% in cold/archive
- **Year 3**: 1PB với intelligent tiering

### 7.2. Scaling Strategies
- **Horizontal**: Add nodes cho Redis, OpenSearch
- **Vertical**: Upgrade instance types
- **Automatic**: Auto-scaling policies

## 8. Cost Optimization

### 8.1. Storage Optimization
- **S3 Intelligent-Tiering**: Automatic cost optimization
- **Reserved Capacity**: Cho predictable workloads
- **Spot Instances**: Cho batch processing

### 8.2. Query Optimization
- **Partition Pruning**: Reduce data scanned
- **Columnar Projection**: Select only needed columns
- **Result Caching**: Reuse frequent query results

## 9. Migration từ Stage 02

### 9.1. Prerequisites
- Stage 02 ETL pipeline stable và tested
- Data quality metrics meeting thresholds
- Storage infrastructure provisioned

### 9.2. Migration Steps
1. **Setup Infrastructure**: Provision all storage services
2. **Configure Lifecycle**: Setup S3 lifecycle policies
3. **Load Historical Data**: Backfill từ Stage 02 output
4. **Enable Streaming**: Connect real-time ingestion
5. **Validate**: Run parallel với old system
6. **Cutover**: Switch downstream consumers

## 10. Success Criteria

### 10.1. Technical Metrics
- Query latency < 1s cho 95% requests
- 99.9% availability cho hot tier
- Zero data loss trong 6 tháng

### 10.2. Business Metrics
- 50% reduction trong storage costs
- 3x improvement trong query performance
- 100% compliance với retention policies

## 11. Risks và Mitigations

### 11.1. Technical Risks
- **Data Loss**: Mitigate với multi-region replication
- **Performance Degradation**: Monitor và auto-scale
- **Schema Evolution**: Version control và migration tools

### 11.2. Operational Risks
- **Cost Overrun**: Budget alerts và cost anomaly detection
- **Compliance Violation**: Automated policy enforcement
- **Security Breach**: Defense in depth strategy

## 12. Next Steps (Stage 04 Preview)

Với nền tảng storage vững chắc từ Stage 03, Stage 04 (Detection Engine) sẽ:
- Leverage hot tier cho real-time anomaly detection
- Use warm tier cho pattern learning
- Access cold tier cho historical baseline
- Build ML models với distributed computing

Storage layer này không chỉ là nơi lưu trữ dữ liệu, mà là một hệ thống thông minh, tự tối ưu, cung cấp dữ liệu đúng lúc, đúng nơi, với chi phí tối ưu cho toàn bộ pipeline phát hiện bất thường và phân tích nguyên nhân gốc rễ.