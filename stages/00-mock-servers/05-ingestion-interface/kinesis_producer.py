"""
Kinesis Producer Module
Sends logs to Kinesis Data Streams
"""
import boto3
import json
import os
from typing import Dict, List, Any
import base64

class KinesisProducer:
    def __init__(self):
        self.endpoint_url = os.environ.get('AWS_ENDPOINT_URL', 'http://localstack:4566')
        self.region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        self.stream_name = os.environ.get('KINESIS_STREAM_NAME', 'stage01-logs-stream')
        self.enabled = os.environ.get('KINESIS_ENABLED', 'false').lower() == 'true'
        
        if self.enabled:
            self.client = boto3.client(
                'kinesis',
                endpoint_url=self.endpoint_url,
                region_name=self.region,
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
            print(f"[Kinesis Producer] Initialized - Stream: {self.stream_name}, Endpoint: {self.endpoint_url}")
        else:
            self.client = None
            print("[Kinesis Producer] Disabled")
    
    def send_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Send logs to Kinesis stream"""
        if not self.enabled or not self.client:
            return {"success": 0, "failed": len(logs), "message": "Kinesis disabled"}
        
        if not logs:
            return {"success": 0, "failed": 0}
        
        success_count = 0
        failed_count = 0
        
        try:
            # Prepare records for batch put
            records = []
            for log in logs:
                partition_key = log.get('service', log.get('source', 'unknown'))
                # Kinesis expects bytes, boto3 handles base64 encoding automatically
                data = json.dumps(log, ensure_ascii=False).encode('utf-8')
                
                records.append({
                    'Data': data,
                    'PartitionKey': partition_key
                })
            
            # Send in batches of 500 (Kinesis limit)
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                response = self.client.put_records(
                    StreamName=self.stream_name,
                    Records=batch
                )
                
                # Count successes and failures
                success_count += len(batch) - response.get('FailedRecordCount', 0)
                failed_count += response.get('FailedRecordCount', 0)
            
            if success_count > 0:
                print(f"✅ [Kinesis Producer] Sent {success_count} logs to {self.stream_name}")
            
            if failed_count > 0:
                print(f"⚠️  [Kinesis Producer] Failed to send {failed_count} logs")
            
        except Exception as e:
            print(f"❌ [Kinesis Producer] Error sending logs: {e}")
            failed_count = len(logs)
        
        return {
            "success": success_count,
            "failed": failed_count
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Kinesis connection"""
        if not self.enabled or not self.client:
            return {
                "success": False,
                "message": "Kinesis producer is disabled"
            }
        
        try:
            response = self.client.describe_stream(StreamName=self.stream_name)
            status = response['StreamDescription']['StreamStatus']
            
            return {
                "success": True,
                "message": f"Connected to stream {self.stream_name}",
                "stream_status": status,
                "shard_count": len(response['StreamDescription']['Shards'])
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to connect: {str(e)}"
            }
