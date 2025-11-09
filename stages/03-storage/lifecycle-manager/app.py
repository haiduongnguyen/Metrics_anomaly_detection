import os
import time
import threading
from datetime import datetime, timezone
from typing import Optional

import boto3
from fastapi import FastAPI

AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localstack:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
WARM_BUCKET = os.getenv("WARM_BUCKET", "md-warm-store")
COLD_BUCKET = os.getenv("COLD_BUCKET", "md-cold-store")
COLD_AFTER_DAYS = float(os.getenv("COLD_AFTER_DAYS", "30"))
ARCHIVE_AFTER_DAYS = float(os.getenv("ARCHIVE_AFTER_DAYS", "365"))
CYCLE_INTERVAL = int(os.getenv("CYCLE_INTERVAL", "15"))

s3 = boto3.client(
    "s3",
    endpoint_url=AWS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

app = FastAPI(title="Stage 03 - Lifecycle Manager", version="1.0.0")

_last_cycle_epoch: int = 0

def ensure_bucket(name: str) -> None:
    try:
        s3.head_bucket(Bucket=name)
    except Exception:
        try:
            s3.create_bucket(Bucket=name)
        except Exception:
            pass

for b in (WARM_BUCKET, COLD_BUCKET):
    ensure_bucket(b)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "lifecycle-manager"}

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
    return {
        "warm_objects": count_objects(WARM_BUCKET),
        "cold_objects": count_objects(COLD_BUCKET),
        "last_cycle_epoch": _last_cycle_epoch,
        "cold_after_days": COLD_AFTER_DAYS,
        "archive_after_days": ARCHIVE_AFTER_DAYS,
    }

def should_cold_transition(last_modified) -> bool:
    try:
        if COLD_AFTER_DAYS <= 0:
            return True
        if not last_modified:
            return False
        now = datetime.now(timezone.utc)
        age_days = (now - last_modified).total_seconds() / 86400.0
        return age_days >= COLD_AFTER_DAYS
    except Exception:
        return False

def lifecycle_loop():
    global _last_cycle_epoch
    while True:
        try:
            paginator = s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=WARM_BUCKET, PaginationConfig={"MaxItems": 50}):
                contents = page.get("Contents", [])
                for obj in contents:
                    key = obj.get("Key")
                    last_modified = obj.get("LastModified")  # datetime with tz
                    if not key:
                        continue
                    if should_cold_transition(last_modified):
                        try:
                            s3.copy_object(
                                Bucket=COLD_BUCKET,
                                CopySource={"Bucket": WARM_BUCKET, "Key": key},
                                Key=key,
                            )
                        except Exception:
                            pass
                break  # process one page per interval
            _last_cycle_epoch = int(time.time())
        except Exception:
            pass
        time.sleep(CYCLE_INTERVAL)

threading.Thread(target=lifecycle_loop, daemon=True).start()