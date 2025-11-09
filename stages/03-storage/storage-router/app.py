import os
import time
import threading
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import boto3
import redis

# Configuration
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localstack:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
TRANSFORMED_LOGS_BUCKET = os.getenv("TRANSFORMED_LOGS_BUCKET", "md-transformed-logs")
TRANSFORMED_METRICS_BUCKET = os.getenv("TRANSFORMED_METRICS_BUCKET", "md-transformed-metrics")
WARM_BUCKET = os.getenv("WARM_BUCKET", "md-warm-store")
COLD_BUCKET = os.getenv("COLD_BUCKET", "md-cold-store")
REDIS_HOST = os.getenv("REDIS_HOST", "redis-hot")
ROUTE_INTERVAL = int(os.getenv("ROUTE_INTERVAL", "10"))

# Clients
s3 = boto3.client(
    "s3",
    endpoint_url=AWS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

# Ensure destination buckets exist (best-effort)
def ensure_bucket(name: str) -> None:
    try:
        s3.head_bucket(Bucket=name)
    except Exception:
        try:
            s3.create_bucket(Bucket=name)
        except Exception:
            # LocalStack might have eventual consistency or region quirks; ignore
            pass

for b in (WARM_BUCKET, COLD_BUCKET):
    ensure_bucket(b)

# Redis may not be ready immediately; handle retry
redis_client: Optional[redis.Redis] = None
for _ in range(20):
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0)
        redis_client.ping()
        break
    except Exception:
        time.sleep(1)
if redis_client is None:
    redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0)

app = FastAPI(title="Stage 03 - Storage Router", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "healthy", "service": "storage-router"}

def count_objects(bucket: str) -> int:
    try:
        paginator = s3.get_paginator("list_objects_v2")
        total = 0
        for page in paginator.paginate(Bucket=bucket):
            total += len(page.get("Contents", []))
        return total
    except Exception:
        return -1

@app.get("/stats")
def stats():
    warm_objects = count_objects(WARM_BUCKET)
    cold_objects = count_objects(COLD_BUCKET)
    try:
        redis_keys = int(redis_client.dbsize())
        last_route_ts = redis_client.get("stage03:last_route_ts")
        last_route = int(last_route_ts) if last_route_ts else 0
        ticks = int(redis_client.get("stage03:route_ticks") or 0)
    except Exception:
        redis_keys = -1
        last_route = 0
        ticks = 0
    return {
        "warm_objects": warm_objects,
        "cold_objects": cold_objects,
        "redis_keys": redis_keys,
        "last_route_epoch": last_route,
        "route_ticks": ticks,
    }

def router_loop():
    while True:
        try:
            # 1) Track route heartbeat in Redis
            try:
                redis_client.set("stage03:last_route_ts", int(time.time()))
                redis_client.incr("stage03:route_ticks")
            except Exception:
                pass

            # 2) Copy small batch from transformed logs -> WARM
            try:
                paginator = s3.get_paginator("list_objects_v2")
                # Process only first small page per interval
                for page in paginator.paginate(
                    Bucket=TRANSFORMED_LOGS_BUCKET, PaginationConfig={"MaxItems": 25}
                ):
                    for obj in page.get("Contents", []):
                        key = obj["Key"]
                        try:
                            s3.copy_object(
                                Bucket=WARM_BUCKET,
                                CopySource={"Bucket": TRANSFORMED_LOGS_BUCKET, "Key": key},
                                Key=key,
                            )
                        except Exception:
                            pass
                    break
            except Exception:
                pass
        except Exception:
            pass
        time.sleep(ROUTE_INTERVAL)

# Background worker
threading.Thread(target=router_loop, daemon=True).start()

@app.get("/")
def index():
    return JSONResponse({"message": "Stage 03 - Storage Router OK", "interval": ROUTE_INTERVAL})