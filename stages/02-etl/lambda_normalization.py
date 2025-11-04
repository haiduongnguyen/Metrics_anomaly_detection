# lambda_normalization.py
import json
import boto3
import pandas as pd
from io import StringIO
from sklearn.preprocessing import MinMaxScaler
from config import DATASETS

s3 = boto3.client("s3")

def lambda_handler(event, context):
    dataset_name = event.get("dataset", "apm_metrics")
    cfg = DATASETS[dataset_name]

    bucket_in, key_in = parse_s3_path(cfg["filtered_s3"])
    bucket_out, key_out = parse_s3_path(cfg["normalized_s3"])

    print(f"[INFO] Normalizing dataset: {dataset_name}")
    obj = s3.get_object(Bucket=bucket_in, Key=key_in)
    df = pd.read_csv(obj["Body"])
    print(f"[INFO] Records loaded: {len(df)}")

    norm_cfg = cfg.get("normalization", {})

    # Convert timestamp
    if norm_cfg.get("timestamp_to_utc", False) and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.tz_localize("UTC")

    # Scale numeric columns
    if "scale" in norm_cfg:
        cols = [c for c in norm_cfg["scale"] if c in df.columns]
        if cols:
            scaler = MinMaxScaler()
            df[cols] = scaler.fit_transform(df[cols])
            print(f"[INFO] Scaled columns: {cols}")

    # Round
    if "round_digits" in norm_cfg:
        df = df.round(norm_cfg["round_digits"])
        print(f"[INFO] Rounded values to {norm_cfg['round_digits']} digits")

    # Write to S3
    out_buffer = StringIO()
    df.to_csv(out_buffer, index=False)
    s3.put_object(Bucket=bucket_out, Key=key_out, Body=out_buffer.getvalue())

    print(f"[INFO] Normalization completed for {dataset_name}")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "dataset": dataset_name,
            "rows_processed": len(df),
            "output_path": cfg["normalized_s3"]
        })
    }

def parse_s3_path(s3_uri):
    s3_uri = s3_uri.replace("s3://", "")
    bucket, key = s3_uri.split("/", 1)
    return bucket, key
