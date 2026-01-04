import json
import boto3
import csv
import io
import operator

s3 = boto3.client("s3")

# operators supported
OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le
}

def load_config():
    """Load local config.json packaged with Lambda code."""
    with open("config.json", "r") as f:
        return json.load(f)


def record_passes_rules(record, config):
    """Apply required fields + allow lists + filter rules."""
    # Required fields must exist
    for field in config.get("required_fields", []):
        if field not in record:
            return False

    # Allowed severity
    sev_allow = config.get("severity_allow")
    if sev_allow and record.get("severity") not in sev_allow:
        return False

    # Allowed service
    svc_allow = config.get("service_allow")
    if svc_allow and record.get("service") not in svc_allow:
        return False

    # filter_rules (generic rule engine)
    for r in config.get("filter_rules", []):
        field = r.get("field")
        op = r.get("operator")
        value = r.get("value")

        # skip invalid rule
        if field not in record or op not in OPS:
            return False

        try:
            if not OPS[op](record[field], value):
                return False
        except:
            return False

    return True


def detect_format(raw):
    """Attempts to auto-detect format: json, jsonl, csv."""
    raw = raw.strip()
    if raw.startswith("{"):
        return "jsonl" if "\n" in raw else "json"
    return "csv"


def lambda_handler(event, context):
    config = load_config()

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]

    print(f"Processing {bucket}/{key}")

    raw_data = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8", errors="ignore")

    input_format = config.get("input_format", "auto")
    if input_format == "auto":
        input_format = detect_format(raw_data)

    print("Detected input format:", input_format)

    filtered = []

    # ------------------------------
    # JSON (single record)
    # ------------------------------
    if input_format == "json":
        try:
            record = json.loads(raw_data)
            if record_passes_rules(record, config):
                filtered.append(record)
        except:
            pass

    # ------------------------------
    # JSON Lines
    # ------------------------------
    elif input_format == "jsonl":
        for line in raw_data.splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if record_passes_rules(record, config):
                    filtered.append(record)
            except:
                continue

    # ------------------------------
    # CSV
    # ------------------------------
    elif input_format == "csv":
        reader = csv.DictReader(io.StringIO(raw_data))
        for row in reader:
            # convert numeric fields automatically
            for k, v in row.items():
                if v and v.isdigit():
                    row[k] = int(v)

            if record_passes_rules(row, config):
                filtered.append(row)

    # ------------------------------
    # SAVE OUTPUT TO S3
    # ------------------------------
    out_key = key.replace("raw/", "filtered/")
    if out_key == key:
        out_key = "filtered/" + key.split("/")[-1]

    output_str = "\n".join(json.dumps(r) for r in filtered)

    s3.put_object(
        Bucket=bucket, 
        Key=out_key, 
        Body=output_str.encode("utf-8")
    )

    print(f"Saved {len(filtered)} filtered records to {out_key}")

    return {
        "statusCode": 200,
        "count": len(filtered),
        "output_key": out_key
    }
