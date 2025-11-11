# lambda_filter.py
import json
import boto3
import pandas as pd
from io import StringIO
from config import DATASETS

s3 = boto3.client("s3")

def parse_s3_path(s3_uri):
    s3_uri = s3_uri.replace("s3://", "")
    bucket, key = s3_uri.split("/", 1)
    return bucket, key

def lambda_handler(event, context):
    dataset_name = event.get("dataset", "apm_metrics")
    cfg = DATASETS[dataset_name]

    bucket_in, key_in = parse_s3_path(cfg["input_s3"])
    bucket_out, key_out = parse_s3_path(cfg["filtered_s3"])

    print(f"[INFO] Processing dataset: {dataset_name}")
    print(f"[INFO] Input: {cfg['input_s3']} → Output: {cfg['filtered_s3']}")

    # Read CSV from S3
    obj = s3.get_object(Bucket=bucket_in, Key=key_in)
    df = pd.read_csv(obj["Body"])
    original_count = len(df)
    print(f"[INFO] Initial rows: {original_count}")

    # Convert datatypes according to schema
    for col, dtype in cfg["schema"].items():
        if col not in df.columns:
            continue
        try:
            if "datetime" in dtype:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            elif dtype == "float":
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif dtype == "bool":
                df[col] = df[col].astype(bool)
            else:
                df[col] = df[col].astype(str)
        except Exception as e:
            print(f"[WARN] Could not cast {col} → {dtype}: {e}")

    f = cfg["filters"]

    # Drop missing values
    if "dropna" in f:
        before = len(df)
        df = df.dropna(subset=f["dropna"])
        print(f"[INFO] Dropped {before - len(df)} rows with NA")

    # Range filtering
    if "range" in f:
        for col, (min_v, max_v) in f["range"].items():
            if col not in df.columns:
                continue
            before = len(df)
            if min_v is not None:
                df = df[df[col] >= min_v]
            if max_v is not None:
                df = df[df[col] <= max_v]
            print(f"[INFO] Filtered {col}, removed {before - len(df)} rows")

    # Remove duplicates
    if f.get("remove_duplicates", False):
        before = len(df)
        df = df.drop_duplicates()
        print(f"[INFO] Removed {before - len(df)} duplicate rows")

    # Timestamp sanity check
    if f.get("timestamp_check", False) and "timestamp" in df.columns:
        now = pd.Timestamp.now(tz="UTC")
        before = len(df)
        df = df[df["timestamp"] <= now]
        print(f"[INFO] Removed {before - len(df)} rows with future timestamps")

    # Save cleaned CSV to S3
    out_buffer = StringIO()
    df.to_csv(out_buffer, index=False)
    s3.put_object(Bucket=bucket_out, Key=key_out, Body=out_buffer.getvalue())

    print(f"[INFO] Final record count: {len(df)}")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "dataset": dataset_name,
            "rows_before": original_count,
            "rows_after": len(df),
            "output_path": cfg["filtered_s3"]
        })
    }
