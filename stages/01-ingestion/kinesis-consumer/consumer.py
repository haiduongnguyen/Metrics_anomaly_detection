"""
Kinesis Consumer Service
Continuously reads from Kinesis stream and writes to S3
Alternative to Lambda for LocalStack local development
"""
import boto3
import json
import time
import base64
from datetime import datetime
import uuid
import os
import signal
import sys
from typing import Dict, List, Any

# Configuration
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', 'http://localstack:4566')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
STREAM_NAME = os.environ.get('STREAM_NAME', 'stage01-logs-stream')
TARGET_BUCKET = os.environ.get('TARGET_BUCKET', 'md-raw-logs')
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '5'))  # seconds
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '100'))

# Initialize boto3 clients
kinesis_client = boto3.client(
    'kinesis',
    endpoint_url=AWS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

s3_client = boto3.client(
    's3',
    endpoint_url=AWS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Graceful shutdown
shutdown_requested = False

def signal_handler(sig, frame):
    global shutdown_requested
    print("\n🛑 Shutdown requested, finishing current batch...")
    shutdown_requested = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def extract_service_name(log: Dict[str, Any]) -> str:
    """Extract service name from log record"""
    return log.get('service', log.get('source', 'unknown'))

def generate_s3_key(log: Dict[str, Any]) -> str:
    """Generate S3 key with partitioning"""
    try:
        timestamp_str = log.get('timestamp', datetime.utcnow().isoformat())
        if isinstance(timestamp_str, str):
            timestamp_str = timestamp_str.replace('Z', '+00:00')
            if '.' in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.split('.')[0])
            else:
                dt = datetime.fromisoformat(timestamp_str.split('+')[0])
        else:
            dt = datetime.utcnow()
    except Exception as e:
        print(f"⚠️  Error parsing timestamp: {e}, using current time")
        dt = datetime.utcnow()
    
    service = extract_service_name(log)
    
    key = (
        f"service={service}/"
        f"year={dt.year}/"
        f"month={dt.month:02d}/"
        f"day={dt.day:02d}/"
        f"hour={dt.hour:02d}/"
        f"part-{uuid.uuid4()}.jsonl"
    )
    
    return key

def write_to_s3(logs: List[Dict[str, Any]]) -> Dict[str, int]:
    """Write logs to S3 with proper partitioning"""
    if not logs:
        return {"success": 0, "failed": 0}
    
    # Group logs by partition
    partitions: Dict[str, List[Dict[str, Any]]] = {}
    
    for log in logs:
        key = generate_s3_key(log)
        base_path = '/'.join(key.split('/')[:-1])
        
        if base_path not in partitions:
            partitions[base_path] = []
        
        partitions[base_path].append(log)
    
    success_count = 0
    failed_count = 0
    
    # Write each partition
    for base_path, partition_logs in partitions.items():
        try:
            content = '\n'.join([json.dumps(log) for log in partition_logs])
            filename = f"part-{uuid.uuid4()}.jsonl"
            full_key = f"{base_path}/{filename}"
            
            s3_client.put_object(
                Bucket=TARGET_BUCKET,
                Key=full_key,
                Body=content.encode('utf-8'),
                ContentType='application/x-ndjson'
            )
            
            success_count += len(partition_logs)
            print(f"✅ Wrote {len(partition_logs)} logs to s3://{TARGET_BUCKET}/{full_key}")
            
        except Exception as e:
            print(f"❌ Error writing partition {base_path}: {e}")
            failed_count += len(partition_logs)
    
    return {"success": success_count, "failed": failed_count}

def get_shard_iterator(stream_name: str, shard_id: str) -> str:
    """Get shard iterator for reading"""
    response = kinesis_client.get_shard_iterator(
        StreamName=stream_name,
        ShardId=shard_id,
        ShardIteratorType='LATEST'
    )
    return response['ShardIterator']

def consume_shard(shard_id: str):
    """Consume records from a shard"""
    print(f"📖 Starting consumption from shard: {shard_id}")
    
    shard_iterator = get_shard_iterator(STREAM_NAME, shard_id)
    records_processed = 0
    empty_polls = 0
    
    while not shutdown_requested:
        try:
            # Get records from Kinesis
            response = kinesis_client.get_records(
                ShardIterator=shard_iterator,
                Limit=BATCH_SIZE
            )
            
            records = response.get('Records', [])
            shard_iterator = response.get('NextShardIterator')
            
            if not shard_iterator:
                print(f"⚠️  Shard {shard_id} has been closed")
                break
            
            if records:
                empty_polls = 0
                logs = []
                
                # Parse records
                for record in records:
                    try:
                        # boto3 Kinesis client returns Data as bytes, already decoded from base64
                        data_field = record.get('Data', b'')
                        if isinstance(data_field, bytes):
                            data = data_field.decode('utf-8')
                        else:
                            # Fallback for string
                            data = str(data_field)
                        
                        log_data = json.loads(data)
                        logs.append(log_data)
                    except Exception as e:
                        print(f"⚠️  Error parsing record: {e}")
                
                # Write to S3
                if logs:
                    result = write_to_s3(logs)
                    records_processed += result['success']
                    
                    print(f"📊 Batch processed: {len(records)} records, {result['success']} written, {result['failed']} failed")
                    print(f"📈 Total processed: {records_processed}")
            
            else:
                empty_polls += 1
                if empty_polls % 10 == 0:
                    print(f"⏳ No new records (checked {empty_polls} times)")
                
                time.sleep(POLL_INTERVAL)
        
        except Exception as e:
            print(f"❌ Error consuming records: {e}")
            time.sleep(POLL_INTERVAL)
    
    print(f"✅ Stopped consuming shard {shard_id}. Total processed: {records_processed}")

def main():
    """Main consumer loop"""
    print("=" * 60)
    print("🚀 Kinesis Consumer Service Starting")
    print("=" * 60)
    print(f"Stream: {STREAM_NAME}")
    print(f"Target Bucket: {TARGET_BUCKET}")
    print(f"Poll Interval: {POLL_INTERVAL}s")
    print(f"Batch Size: {BATCH_SIZE}")
    print("=" * 60)
    
    # Wait for Kinesis to be ready
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = kinesis_client.describe_stream(StreamName=STREAM_NAME)
            stream_status = response['StreamDescription']['StreamStatus']
            
            if stream_status == 'ACTIVE':
                print(f"✅ Stream {STREAM_NAME} is ACTIVE")
                break
            else:
                print(f"⏳ Stream status: {stream_status}, waiting...")
                time.sleep(5)
        
        except Exception as e:
            print(f"⚠️  Attempt {attempt + 1}/{max_retries}: Error connecting to Kinesis: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                print("❌ Failed to connect to Kinesis stream")
                sys.exit(1)
    
    # Get shards
    response = kinesis_client.describe_stream(StreamName=STREAM_NAME)
    shards = response['StreamDescription']['Shards']
    
    print(f"📑 Found {len(shards)} shard(s)")
    
    # For simplicity, consume from first shard
    # In production, use multi-threading or KCL for multiple shards
    if shards:
        shard_id = shards[0]['ShardId']
        print(f"📖 Consuming from shard: {shard_id}")
        consume_shard(shard_id)
    else:
        print("❌ No shards found in stream")
        sys.exit(1)
    
    print("\n✅ Kinesis Consumer Service stopped gracefully")

if __name__ == '__main__':
    main()
