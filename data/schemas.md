Dựa trên dữ liệu Elasticsearch bạn cung cấp, đây là schemas chi tiết và đầy đủ:

## **Main Schema Structure**

```json
{
  "took": "integer",
  "timed_out": "boolean",
  "_shards": {
    "total": "integer",
    "successful": "integer",
    "skipped": "integer",
    "failed": "integer",
    "failures": [
      {
        "shard": "integer",
        "index": "string",
        "node": "string",
        "reason": {
          "type": "string",
          "reason": "string",
          "index_uuid": "string",
          "index": "string"
        }
      }
    ]
  },
  "hits": {
    "total": "integer",
    "max_score": "null | float",
    "hits": [
      {
        "_index": "string",
        "_type": "string",
        "_id": "string",
        "_score": "null | float",
        "_source": {
          "kubernetes": {
            "container_image_id": "string",
            "container_name": "string",
            "namespace_id": "string (UUID)",
            "flat_labels": ["string"],
            "pod_ip": "string (IP address)",
            "host": "string",
            "master_url": "string (URL)",
            "pod_id": "string (UUID)",
            "namespace_labels": {
              "kubernetes_io/metadata_name": "string",
              "argo_cntk/instance": "string",
              "openshift_io/cluster-monitoring": "string",
              "[dynamic_key]": "string"
            },
            "container_image": "string",
            "namespace_name": "string",
            "pod_name": "string"
          },
          "viaq_msg_id": "string (UUID)",
          "level": "string (info|error|debug|warn|unknown)",
          "openshift": {
            "sequence": "integer"
          },
          "message": "string (multiline text)",
          "docker": {
            "container_id": "string (hex)"
          },
          "hostname": "string",
          "log_type": "string",
          "@timestamp": "string (ISO 8601 datetime)",
          "pipeline_metadata": {
            "collector": {
              "received_at": "string (ISO 8601 datetime)",
              "name": "string",
              "inputname": "string",
              "version": "string",
              "ipaddr4": "string (IP address)"
            }
          }
        },
        "sort": ["integer (timestamp in milliseconds)"]
      }
    ]
  }
}
```

## **Detailed Field Descriptions**

### **Top Level Fields**
- `took`: Thời gian query (ms)
- `timed_out`: Query có timeout không
- `_shards`: Thông tin về shards
  - `total`: Tổng số shards
  - `successful`: Số shards thành công
  - `skipped`: Số shards bỏ qua
  - `failed`: Số shards thất bại
  - `failures`: Array các lỗi shard (optional)

### **Hits Object**
- `total`: Tổng số documents tìm được
- `max_score`: Score cao nhất (null nếu không scoring)
- `hits`: Array các documents

### **Document Fields (_source)**

#### **kubernetes** (object)
```typescript
{
  container_image_id: string,        // SHA256 hash của image
  container_name: string,            // Tên container
  namespace_id: string,              // UUID của namespace
  flat_labels: string[],             // Array các labels (key=value format)
  pod_ip: string,                    // IP của pod (IPv4)
  host: string,                      // Hostname của worker node
  master_url: string,                // URL của K8s master
  pod_id: string,                    // UUID của pod
  namespace_labels: {                // Dynamic object
    [key: string]: string
  },
  container_image: string,           // Full image name với tag
  namespace_name: string,            // Tên namespace
  pod_name: string                   // Tên pod
}
```

#### **Other Fields**
```typescript
{
  viaq_msg_id: string,              // UUID của message
  level: "info" | "error" | "debug" | "warn" | "unknown",
  openshift: {
    sequence: number                 // Sequence number của log
  },
  message: string,                   // Nội dung log (có thể multiline)
  docker: {
    container_id: string             // Docker container ID (hex)
  },
  hostname: string,                  // Hostname
  log_type: string,                  // Loại log (thường là "application")
  "@timestamp": string,              // ISO 8601 datetime với timezone
  pipeline_metadata: {
    collector: {
      received_at: string,           // ISO 8601 datetime
      name: string,                  // Tên collector (fluentd)
      inputname: string,             // Input plugin name
      version: string,               // Version string
      ipaddr4: string                // IPv4 address
    }
  }
}
```

## **Data Type Specifications**

### **String Formats**
- **UUID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **IP Address**: `xxx.xxx.xxx.xxx`
- **ISO 8601 DateTime**: `YYYY-MM-DDTHH:mm:ss.SSSSSSSSS+00:00`
- **Container ID**: 64 character hex string
- **SHA256**: `sha256:` + 64 character hex string

### **Numeric Ranges**
- `took`: 0 - 10000 ms
- `sequence`: 0 - 999999999
- `timestamp`: Unix timestamp in milliseconds

### **Enum Values**
- `log_type`: "application", "infrastructure"
- `level`: "info", "error", "debug", "warn", "unknown"
- `_type`: "_doc"

## **Sample Valid Values**

```json
{
  "container_image_id": "nhs-registry.pvcb.vn/nhs/baas/investment-saving/egold/cordite-nms@sha256:de533155df7fa0286e06aa798dde193755465e0b9fdd6fed37eb77f96608b6cb",
  "namespace_id": "71d5dbfe-5e49-47da-a7cb-f4f70aa05466",
  "pod_ip": "10.133.6.89",
  "viaq_msg_id": "NjQ2YmE4MjYtYTY2ZS00YjM3LWI3OTctYmJiYTI1Y2YwYjZj",
  "@timestamp": "2025-10-20T07:26:40.532730929+00:00",
  "docker.container_id": "91d5f9d450393375cd88193f568efa3906d41ca2f18f5701fd4bb9af83988de9"
}
```

Schema này bao gồm tất cả các trường có trong dữ liệu mẫu của bạn, với các kiểu dữ liệu chính xác và mô tả chi tiết.