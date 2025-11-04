# config.py
# Central configuration for ingestion and ETL pipelines

DATASETS = {
    # ===============================
    # 1️⃣ Application Performance Metrics
    # ===============================
    "apm_metrics": {
        "input_s3": "s3://vpbank-hackathon/raw/apm_metrics_3k.csv",
        "filtered_s3": "s3://vpbank-hackathon/processed/apm_metrics_clean.csv",
        "normalized_s3": "s3://vpbank-hackathon/transformed/apm_metrics_norm.csv",

        "schema": {
            "timestamp": "datetime64[ns]",
            "service_name": "str",
            "host": "str",
            "cpu_percent": "float",
            "mem_percent": "float",
            "disk_util_percent": "float",
            "disk_read_mb_s": "float",
            "disk_write_mb_s": "float",
            "net_in_mb_s": "float",
            "net_out_mb_s": "float",
            "rps": "float",
            "latency_p95_ms": "float",
            "error_rate_percent": "float",
            "gc_pause_ms": "float",
            "packet_loss_percent": "float",
            "is_anomaly": "bool",
            "anomaly_type": "str"
        },

        "filters": {
            "range": {
                "cpu_percent": [0, 100],
                "mem_percent": [0, 100],
                "disk_util_percent": [0, 100],
                "error_rate_percent": [0, 100],
                "packet_loss_percent": [0, 100],
                "latency_p95_ms": [0, None]
            },
            "dropna": [
                "cpu_percent", "mem_percent",
                "latency_p95_ms", "error_rate_percent"
            ],
            "remove_duplicates": True,
            "timestamp_check": True
        },

        "normalization": {
            "timestamp_to_utc": True,
            "scale": [
                "cpu_percent", "mem_percent", "disk_util_percent",
                "disk_read_mb_s", "disk_write_mb_s",
                "net_in_mb_s", "net_out_mb_s",
                "rps", "latency_p95_ms", "error_rate_percent",
                "gc_pause_ms", "packet_loss_percent"
            ],
            "round_digits": 4
        }
    },

    # ===============================
    # 2️⃣ Application Logs Dataset
    # ===============================
    "app_logs": {
        "input_s3": "s3://vpbank-hackathon/raw/app_logs_5k.csv",
        "filtered_s3": "s3://vpbank-hackathon/processed/app_logs_clean.csv",
        "normalized_s3": "s3://vpbank-hackathon/transformed/app_logs_norm.csv",

        "schema": {
            "timestamp": "datetime64[ns]",
            "service_name": "str",
            "host": "str",
            "log_level": "str",
            "message": "str",
            "request_id": "str",
            "response_time_ms": "float",
            "error_code": "str",
            "user_id": "str",
            "trace_id": "str",
            "is_anomaly": "bool",
            "anomaly_type": "str"
        },

        "filters": {
            "dropna": ["timestamp", "message"],
            "remove_duplicates": True,
            "timestamp_check": True
        },

        "normalization": {
            "timestamp_to_utc": True,
            "round_digits": 3
        }
    }
}
