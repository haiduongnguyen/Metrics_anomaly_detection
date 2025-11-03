# HỆ THỐNG MÔ PHỎNG ANOMALY LOGS CHO NGÂN HÀNG
## Tài liệu Thiết kế Kiến trúc và Services

---

## 1. TỔNG QUAN KIẾN TRÚC HỆ THỐNG

### 1.1 Mục tiêu thiết kế
Xây dựng hệ thống microservices có khả năng mô phỏng toàn diện 200 loại bất thường trong ngân hàng, tạo ra logs thực tế để inject vào lớp ingestion phục vụ mục đích testing, training và validation cho hệ thống monitoring và detection.

### 1.2 Nguyên tắc thiết kế
- **Modular Architecture**: Mỗi service độc lập, có thể scale riêng biệt
- **Event-Driven**: Sử dụng message queue để đảm bảo loosely coupled
- **Configurable**: Mọi tham số có thể điều chỉnh qua configuration
- **Realistic Simulation**: Logs phải giống thực tế về format, timing và correlation
- **Performance Optimized**: Có thể generate 10,000+ logs/giây khi cần

### 1.3 Tech Stack khuyến nghị
- **Message Queue**: Apache Kafka (high throughput, distributed)
- **Time-series Database**: InfluxDB hoặc TimescaleDB
- **Cache**: Redis (cho state management và rate limiting)
- **Container Orchestration**: Kubernetes
- **API Gateway**: Kong hoặc Traefik
- **Monitoring**: Prometheus + Grafana
- **Log Processing**: ELK Stack (Elasticsearch, Logstash, Kibana)

---

## 2. DANH SÁCH 5 SERVICES TỐI THIỂU

### 2.1 **SCENARIO ORCHESTRATOR SERVICE**

#### Vai trò chính:
Service trung tâm điều phối toàn bộ quá trình mô phỏng, quản lý lifecycle của các kịch bản bất thường và điều phối các service khác.

#### Chức năng chi tiết:

**A. Scenario Management**
- Quản lý catalog 200 anomaly scenarios với metadata đầy đủ:
  - Scenario ID, name, category (Technical/Business/Security)
  - Severity level (Critical/High/Medium/Low)
  - Default parameters và constraints
  - Dependencies và correlations với scenarios khác
- Lưu trữ scenario templates dạng JSON/YAML có thể version control
- Support scenario composition (kết hợp nhiều scenarios thành campaign)

**B. Execution Control**
- Schedule và trigger scenarios theo multiple modes:
  - **Manual**: User kích hoạt qua UI
  - **Scheduled**: Cron-based scheduling
  - **Continuous**: Random generation với configured rate
  - **Reactive**: Trigger dựa trên events/conditions
- Quản lý execution state (running, paused, completed, failed)
- Support parallel execution của multiple scenarios
- Implement circuit breaker pattern để prevent overload

**C. Configuration Management**
- Central configuration store cho tất cả scenarios:
  ```yaml
  scenario_001:
    name: "CPU Spike Attack"
    category: "Technical"
    severity: "HIGH"
    default_params:
      spike_percentage: 85
      duration_minutes: 5
      affected_servers: 3
      pattern: "gradual_increase"
  ```
- Override configuration per execution
- Environment-specific configurations (dev/staging/prod)
- Feature flags để enable/disable specific scenarios

**D. Coordination và Communication**
- Publish scenario events qua Kafka topics:
  - `scenario.started`
  - `scenario.configured`
  - `scenario.completed`
  - `scenario.failed`
- Coordinate với Pattern Generator để trigger log generation
- Sync với State Manager để maintain consistency
- API endpoints cho Frontend integration

#### Tại sao service này tối thiểu cần thiết:
- Là "brain" của hệ thống, không có nó không thể coordinate 200 scenarios
- Đảm bảo consistency và prevent conflicts giữa scenarios
- Enable complex multi-scenario campaigns
- Provide single point of control cho operators

---

### 2.2 **PATTERN GENERATOR SERVICE**

#### Vai trò chính:
Chịu trách nhiệm generate các patterns và data thực tế cho từng loại anomaly, đảm bảo logs có tính authentic và realistic.

#### Chức năng chi tiết:

**A. Pattern Libraries**
Maintain comprehensive pattern libraries cho từng category:

**Technical Patterns (90 cases)**
- **Infrastructure patterns**: CPU spikes, memory leaks, disk I/O bottlenecks
  - Gaussian distribution cho gradual increase
  - Step functions cho sudden spikes
  - Sawtooth patterns cho periodic issues
- **Network patterns**: Latency variations, packet loss, connection drops
  - Poisson distribution cho random network events
  - Exponential backoff cho retry patterns
- **Database patterns**: Slow queries, deadlocks, replication lag
  - Query execution time distributions
  - Lock contention patterns
  - Replication delay curves

**Business Patterns (90 cases)**
- **Transaction patterns**: Volume spikes, unusual amounts, velocity changes
  - Time-series patterns matching real banking cycles
  - Seasonal adjustments (Tết, payroll dates)
  - Fraud pattern signatures
- **User behavior patterns**: Login anomalies, navigation irregularities
  - Markov chains cho user journey simulation
  - Behavioral biometrics patterns
- **Campaign patterns**: Flash sales, holiday surges
  - Historical data-based patterns
  - Market event correlations

**Security Patterns (20 cases)**
- **Attack patterns**: DDoS, brute force, SQL injection
  - Attack vector distributions
  - Botnet behavior simulation
  - Exploit attempt patterns
- **Fraud patterns**: ATO, phishing, social engineering
  - Fraud ring network patterns
  - Money mule transaction flows

**B. Data Generation Engine**
- **Synthetic data generation** với constraints:
  - Valid Vietnam phone numbers (09x, 03x, 07x, 08x)
  - Realistic Vietnamese names từ database
  - Valid bank account numbers theo chuẩn
  - IP addresses từ Vietnam ISP ranges
  - Transaction amounts theo distribution thực tế
  
- **Correlation engine** để ensure relationships:
  - Account balance phải >= transaction amount
  - Transaction time phải trong business hours cho certain types
  - Geographic correlation (IP location ~ transaction location)
  - Device fingerprint consistency per user

- **Temporal patterns**:
  - Respect Vietnam timezone (GMT+7)
  - Business hours patterns (8:00-17:00)
  - Weekend/holiday adjustments
  - Seasonal variations

**C. Statistical Models**
- **Distribution functions** cho realistic randomness:
  - Normal distribution cho regular transactions
  - Power law cho extreme events
  - Exponential cho inter-arrival times
  - Beta distribution cho conversion rates
  
- **Time-series models**:
  - ARIMA cho transaction volume forecasting
  - Seasonal decomposition
  - Trend analysis với drift

- **Anomaly injection algorithms**:
  ```
  Anomaly Score = Base Score × Severity Weight × Random Factor
  Where:
  - Base Score = predefined per anomaly type (0-100)
  - Severity Weight = {Low: 0.3, Medium: 0.6, High: 0.9, Critical: 1.0}
  - Random Factor = Normal(1.0, 0.2) for variation
  ```

**D. Pattern Composition**
- Combine multiple patterns cho complex scenarios:
  - DDoS + System overload + Database connection exhaustion
  - Account takeover + Fraudulent transactions + Money transfer
- Maintain pattern dependencies và sequencing
- Support pattern inheritance và variation

#### Tại sao service này tối thiểu cần thiết:
- Là "heart" của realism - không có realistic patterns, logs sẽ không có giá trị
- Cover được complexity của 200 scenarios với reusable patterns
- Ensure statistical validity cho ML training
- Enable correlation analysis và cascade simulation

---

### 2.3 **LOG SYNTHESIS ENGINE**

#### Vai trò chính:
Transform patterns và data từ Pattern Generator thành actual log entries với proper formatting, structure và metadata ready cho ingestion.

#### Chức năng chi tiết:

**A. Log Format Templates**
Maintain templates cho các log formats phổ biến:

**Application Logs**
```json
{
  "timestamp": "2024-01-15T09:23:45.123Z",
  "level": "ERROR",
  "service": "payment-service",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "span_id": "7a0b7c0d",
  "user_id": "USR2024001",
  "session_id": "sess_abc123",
  "message": "Payment processing failed",
  "error": {
    "type": "InsufficientFundsException",
    "code": "PAY_ERR_001",
    "details": "Available balance: 100000 VND, Required: 500000 VND"
  },
  "context": {
    "transaction_id": "TXN20240115092345",
    "amount": 500000,
    "currency": "VND",
    "merchant": "MERCHANT_001"
  }
}
```

**Security Logs**
```json
{
  "timestamp": "2024-01-15T09:23:45.123Z",
  "event_type": "authentication_failure",
  "severity": "WARNING",
  "source_ip": "113.161.78.101",
  "user_agent": "Mozilla/5.0...",
  "authentication": {
    "method": "password",
    "attempts": 3,
    "account": "user@example.com",
    "reason": "invalid_credentials"
  },
  "risk_score": 75,
  "geo_location": {
    "country": "VN",
    "city": "Ho Chi Minh City",
    "coordinates": [10.8231, 106.6297]
  }
}
```

**Transaction Logs**
```json
{
  "timestamp": "2024-01-15T09:23:45.123Z",
  "transaction": {
    "id": "TXN20240115092345",
    "type": "transfer",
    "status": "completed",
    "amount": 1000000,
    "currency": "VND",
    "from_account": "****1234",
    "to_account": "****5678",
    "channel": "mobile_app"
  },
  "processing": {
    "duration_ms": 1250,
    "gateway": "VNPAY",
    "authorization_code": "AUTH123"
  },
  "anomaly_indicators": {
    "velocity_score": 0.8,
    "amount_deviation": 2.5,
    "time_deviation": 1.2
  }
}
```

**B. Log Enrichment Pipeline**

**Metadata Enrichment**
- Add correlation IDs để trace across services
- Inject request/response headers
- Add infrastructure metadata (pod name, node, cluster)
- Include version information

**Context Enrichment**
- User profile data (customer segment, account age)
- Historical context (previous transaction count, average amount)
- Business context (campaign active, promotion code)
- Risk context (fraud score, AML flags)

**Anomaly Markers**
- Inject anomaly indicators vào logs:
  - Anomaly type và severity
  - Deviation scores
  - Statistical outlier markers
  - Pattern matching results

**C. Format Conversion**

Support multiple output formats:
- **JSON**: Structured, parseable
- **Syslog**: RFC5424 compliant
- **CSV**: For batch analysis
- **Avro/Parquet**: For big data processing
- **Protobuf**: For high-performance scenarios

Format conversion rules:
```
JSON → Syslog: Flatten nested objects, maintain priority levels
JSON → CSV: Normalize nested structures, handle arrays
JSON → Avro: Schema evolution support, compression
```

**D. Log Correlation và Sequencing**

**Transaction Flow Correlation**
- Link logs across transaction lifecycle:
  - Authentication → Authorization → Processing → Settlement
- Maintain parent-child relationships
- Preserve causality chains

**Session Correlation**
- Group logs by user session
- Track user journey across services
- Maintain session state consistency

**Temporal Sequencing**
- Ensure proper timestamp ordering
- Handle clock skew across services
- Maintain event sequence integrity

#### Tại sao service này tối thiểu cần thiết:
- Bridge giữa abstract patterns và concrete logs
- Ensure logs compatible với existing monitoring tools
- Enable traceability và correlation analysis
- Critical cho forensics và incident investigation

---

### 2.4 **STATE MANAGER SERVICE**

#### Vai trò chính:
Maintain global state consistency, manage entity lifecycles, và ensure realistic state transitions across all simulations.

#### Chức năng chi tiết:

**A. Entity State Management**

**User State**
```yaml
user_001:
  status: active
  login_state: logged_in
  session_started: "2024-01-15T09:00:00Z"
  failed_login_attempts: 0
  current_location: "Ho Chi Minh City"
  device_fingerprint: "device_xyz"
  risk_level: low
  recent_transactions: [...]
  account_balance: 5000000
```

**Account State**
- Balance tracking với transaction consistency
- Hold/freeze status
- Limit utilization
- Recent activity window

**System State**
- Service health status
- Resource utilization levels
- Circuit breaker states
- Rate limiter counters

**B. State Transition Engine**

**Valid State Transitions**
```
Account States:
  active → suspended (violation detected)
  suspended → under_review (investigation started)
  under_review → active (cleared)
  under_review → closed (fraud confirmed)
  
Session States:
  none → authenticating → authenticated → active → expired
  authenticating → failed (max attempts)
  active → locked (suspicious activity)
```

**Transition Validation Rules**
- Enforce business rules (không thể withdraw > balance)
- Validate temporal constraints (session timeout)
- Check dependencies (không thể transfer từ frozen account)

**State Consistency Guarantees**
- ACID properties cho critical state changes
- Eventual consistency cho non-critical updates
- Conflict resolution strategies

**C. Historical State Tracking**

**State History Store**
- Maintain state snapshots theo time intervals
- Track state change events với metadata
- Support time-travel queries

**Audit Trail**
```json
{
  "entity_id": "user_001",
  "entity_type": "user",
  "state_change": {
    "from": "active",
    "to": "suspended",
    "timestamp": "2024-01-15T09:23:45Z",
    "reason": "suspicious_activity",
    "changed_by": "fraud_detection_system"
  }
}
```

**Rollback Capability**
- Restore previous states khi cần
- Undo cascade changes
- Maintain state version history

**D. State Synchronization**

**Cross-Service Sync**
- Broadcast state changes qua event bus
- Implement eventual consistency patterns
- Handle network partitions gracefully

**Cache Synchronization**
- Update Redis cache với latest states
- Implement cache invalidation strategies
- Handle cache misses và rebuilds

**Database Persistence**
- Periodic snapshots to database
- Write-ahead logging cho durability
- Implement checkpointing

#### Tại sao service này tối thiểu cần thiết:
- Prevent impossible scenarios (withdraw từ empty account)
- Ensure simulation realism và consistency
- Enable stateful testing scenarios
- Critical cho multi-step attack simulations

---

### 2.5 **INGESTION INTERFACE SERVICE**

#### Vai trò chính:
Gateway service handle việc inject logs vào target systems, manage throughput, và ensure reliable delivery.

#### Chức năng chi tiết:

**A. Multi-Protocol Support**

**Kafka Producer**
```yaml
kafka_config:
  brokers: ["kafka1:9092", "kafka2:9092"]
  topics:
    application_logs: "app-logs"
    security_logs: "security-logs"
    transaction_logs: "transaction-logs"
  producer_settings:
    acks: "all"
    compression: "snappy"
    batch_size: 16384
    linger_ms: 10
    retries: 3
```

**HTTP/REST Endpoints**
- Bulk insert APIs
- Streaming endpoints (Server-Sent Events)
- Webhook receivers
- GraphQL subscriptions

**Direct Database Writes**
- Batch inserts với prepared statements
- Bulk copy operations
- Optimized for time-series databases

**File-Based Ingestion**
- Log file rotation và shipping
- S3/MinIO uploads
- FTP/SFTP transfers
- Network shares

**B. Rate Control và Throttling**

**Adaptive Rate Limiting**
```
Target Rate = Base Rate × Load Factor × Time Factor

Where:
- Base Rate = configured logs/second (e.g., 1000)
- Load Factor = 1.0 - (current_cpu_usage / max_cpu_usage)
- Time Factor = time-of-day adjustment (peak hours = 1.5, off-peak = 0.5)
```

**Backpressure Handling**
- Monitor target system capacity
- Implement exponential backoff
- Queue overflow protection
- Circuit breaker pattern

**Burst Control**
- Token bucket algorithm cho burst allowance
- Sliding window rate limiting
- Adaptive burst sizing based on target response

**C. Delivery Guarantees**

**At-Least-Once Delivery**
- Message acknowledgment tracking
- Retry với exponential backoff
- Dead letter queue cho failed messages
- Duplicate detection tại receiver

**Ordering Guarantees**
- Preserve timestamp ordering
- Partition key-based ordering (Kafka)
- Sequence number tracking
- Out-of-order detection và handling

**Batch Optimization**
```
Optimal Batch Size = min(
  Max Batch Size,
  Target Throughput × Batch Window,
  Available Memory / Average Message Size
)
```

**D. Monitoring và Observability**

**Ingestion Metrics**
```json
{
  "throughput": {
    "current_rate": 5000,
    "target_rate": 10000,
    "unit": "logs/second"
  },
  "latency": {
    "p50": 10,
    "p95": 25,
    "p99": 50,
    "unit": "milliseconds"
  },
  "errors": {
    "rate": 0.01,
    "types": {
      "timeout": 5,
      "rejected": 2,
      "malformed": 1
    }
  },
  "backlog": {
    "size": 1000,
    "age_seconds": 30
  }
}
```

**Health Checks**
- Target system connectivity
- Authentication validation
- Quota và limit checks
- Performance benchmarks

**Alerting Rules**
- Throughput < 80% of target
- Error rate > 1%
- Backlog age > 60 seconds
- Target system unavailable

#### Tại sao service này tối thiểu cần thiết:
- Final mile delivery - không có nó logs không reach target
- Handle impedance mismatch giữa generation và consumption rates
- Ensure reliable delivery despite failures
- Enable multiple destination support

---

## 3. INTEGRATION VÀ DATA FLOW

### 3.1 End-to-End Flow Diagram

```
Frontend UI
    ↓ (1) Select & Configure Scenario
Scenario Orchestrator
    ↓ (2) Trigger Pattern Generation
Pattern Generator
    ↓ (3) Send Patterns & Data
Log Synthesis Engine
    ↓ (4) Generate Formatted Logs
    ↓ (5) Update States
State Manager
    ↓ (6) Persist State Changes
    ↓ (7) Ready for Ingestion
Ingestion Interface
    ↓ (8) Inject to Targets
Target Systems (Kafka, ELK, Databases)
```

### 3.2 Scenario Execution Lifecycle

**Phase 1: Initialization**
1. User selects scenario từ catalog
2. Configure parameters (severity, duration, volume)
3. Orchestrator validates configuration
4. Check system capacity và resources

**Phase 2: Preparation**
1. Pattern Generator loads relevant patterns
2. State Manager initializes entities
3. Log Synthesis prepares templates
4. Ingestion Interface establishes connections

**Phase 3: Execution**
1. Generate events theo configured rate
2. Synthesize logs với proper formatting
3. Update states để maintain consistency
4. Inject logs vào target systems

**Phase 4: Monitoring**
1. Track execution progress
2. Monitor system health
3. Adjust rate nếu cần
4. Handle errors và retries

**Phase 5: Completion**
1. Graceful shutdown của generation
2. Flush remaining logs
3. Final state persistence
4. Generate execution report

---

## 4. CONFIGURATION EXAMPLES

### 4.1 Scenario Configuration

```yaml
# DDoS Attack Simulation
scenario:
  id: "SEC_004"
  name: "DDoS Attack Pattern"
  category: "Security"
  severity: "CRITICAL"
  
  parameters:
    attack_type: "http_flood"
    target_endpoints: ["/api/login", "/api/transfer"]
    request_rate:
      normal: 100  # requests/second
      attack: 10000  # requests/second
    source_ips:
      count: 1000
      distribution: "random"
      geography: ["CN", "RU", "KP"]  # High-risk countries
    duration:
      ramp_up: 60  # seconds
      sustained: 300  # seconds
      ramp_down: 30  # seconds
    
  patterns:
    request_pattern: "aggressive"
    user_agent: "bot_signatures"
    payload: "minimal"
    
  correlation:
    system_impact:
      cpu_spike: true
      memory_pressure: true
      connection_exhaustion: true
```

### 4.2 Pattern Configuration

```yaml
# Transaction Fraud Pattern
pattern:
  id: "FRAUD_001"
  name: "Card Testing Pattern"
  
  sequence:
    - phase: "testing"
      transactions:
        count: 10-20
        amount: "1000-10000"  # VND
        interval: "1-5"  # seconds
        success_rate: 0.3
        
    - phase: "validation"
      delay: "30-60"  # seconds
      
    - phase: "exploitation"
      transactions:
        count: 1-3
        amount: "10000000-50000000"  # VND
        interval: "immediate"
        channels: ["online", "atm"]
```

### 4.3 Log Format Configuration

```yaml
log_format:
  type: "transaction"
  structure: "json"
  
  fields:
    mandatory:
      - timestamp: "ISO8601"
      - transaction_id: "UUID"
      - amount: "number"
      - currency: "string(3)"
      - status: "enum[success,failed,pending]"
      
    optional:
      - user_id: "string"
      - session_id: "string"
      - device_id: "string"
      - location: "object"
      
    anomaly_markers:
      - anomaly_score: "float(0-100)"
      - anomaly_type: "string"
      - deviation_metrics: "object"
```

---

## 5. DEPLOYMENT VÀ SCALING

### 5.1 Resource Requirements

```yaml
# Minimum Requirements (Dev/Test)
services:
  scenario_orchestrator:
    instances: 1
    cpu: 2 cores
    memory: 4GB
    storage: 10GB
    
  pattern_generator:
    instances: 2
    cpu: 4 cores
    memory: 8GB
    storage: 20GB
    
  log_synthesis:
    instances: 3
    cpu: 4 cores
    memory: 8GB
    storage: 50GB
    
  state_manager:
    instances: 2
    cpu: 2 cores
    memory: 8GB
    storage: 100GB (SSD)
    
  ingestion_interface:
    instances: 3
    cpu: 4 cores
    memory: 4GB
    storage: 20GB

# Production Scale (10K logs/second)
services:
  scenario_orchestrator:
    instances: 3 (HA)
    cpu: 8 cores
    memory: 16GB
    
  pattern_generator:
    instances: 10
    cpu: 16 cores
    memory: 32GB
    
  log_synthesis:
    instances: 20
    cpu: 16 cores
    memory: 32GB
    
  state_manager:
    instances: 5
    cpu: 8 cores
    memory: 32GB
    redis_cluster: 6 nodes
    
  ingestion_interface:
    instances: 15
    cpu: 16 cores
    memory: 16GB
```

### 5.2 Scaling Strategy

**Horizontal Scaling Triggers**
- CPU utilization > 70%
- Memory utilization > 80%
- Queue depth > 10,000 messages
- Response latency > 500ms

**Service-Specific Scaling**
- Pattern Generator: Scale based on scenario complexity
- Log Synthesis: Scale based on log volume
- Ingestion Interface: Scale based on target throughput
- State Manager: Scale Redis cluster for state volume

---

## 6. MONITORING VÀ OPERATIONS

### 6.1 Key Metrics Dashboard

**System Health**
- Service availability (target: 99.9%)
- API response time (target: < 200ms)
- Error rate (target: < 0.1%)
- Resource utilization

**Simulation Metrics**
- Active scenarios count
- Log generation rate (logs/second)
- Pattern coverage (% of 200 anomalies tested)
- State consistency score

**Ingestion Metrics**
- Throughput (actual vs target)
- Delivery success rate
- Backlog size và age
- Target system health

### 6.2 Operational Procedures

**Daily Operations**
- Review overnight simulation runs
- Check error logs và alerts
- Verify state consistency
- Update scenario configurations

**Weekly Operations**
- Analyze pattern effectiveness
- Review resource utilization trends
- Update threat intelligence patterns
- Conduct failover tests

**Monthly Operations**
- Full system backup
- Performance benchmarking
- Security audit
- Scenario catalog review và update

---

## 7. FRONTEND INTEGRATION

### 7.1 User Interface Components

**Scenario Selection**
- Searchable catalog với 200 anomalies
- Category filters (Technical/Business/Security)
- Severity filters (Critical/High/Medium/Low)
- Favorites và recent scenarios

**Configuration Panel**
- Visual parameter editors
- Preset configurations
- Advanced JSON editor
- Validation và preview

**Execution Control**
- Start/Stop/Pause controls
- Progress indicators
- Real-time metrics display
- Log preview window

**Analysis Dashboard**
- Generated log statistics
- Anomaly distribution charts
- System performance metrics
- Export capabilities

### 7.2 API Endpoints

```yaml
# Core APIs
GET /api/scenarios
  - List all 200 scenarios với metadata
  
POST /api/scenarios/{id}/execute
  - Start scenario execution
  
GET /api/executions/{id}/status
  - Get execution progress
  
POST /api/executions/{id}/stop
  - Stop running execution
  
GET /api/logs/preview
  - Preview generated logs
  
POST /api/logs/export
  - Export logs (CSV/JSON)
```

---

## 8. SECURITY CONSIDERATIONS

### 8.1 Access Control
- Role-based access (Admin/Operator/Viewer)
- API authentication (OAuth2/JWT)
- Audit logging cho all operations
- Encryption cho sensitive data

### 8.2 Isolation
- Network segmentation
- Container isolation
- Resource quotas
- Sandboxed execution environment

### 8.3 Data Protection
- Anonymization của PII trong logs
- Encryption at rest và in transit
- Secure deletion của test data
- Compliance với data regulations

---

## 9. CONCLUSION

Hệ thống 5 services này đã được thiết kế để:

1. **Comprehensive Coverage**: Cover toàn bộ 200 anomaly cases với realistic patterns
2. **Scalability**: Có thể generate từ 100 đến 10,000+ logs/second
3. **Flexibility**: Dễ dàng configure và customize qua Frontend
4. **Realism**: Tạo logs không thể phân biệt với production logs
5. **Maintainability**: Modular design cho phép easy updates và extensions

Với architecture này, teams có thể:
- Test detection systems với comprehensive scenarios
- Train ML models với diverse anomaly patterns
- Validate monitoring và alerting pipelines
- Conduct security drills và incident response training
- Ensure system resilience qua chaos engineering

Hệ thống đảm bảo mọi test scenario realistic, repeatable, và valuable cho improving banking system security và reliability.