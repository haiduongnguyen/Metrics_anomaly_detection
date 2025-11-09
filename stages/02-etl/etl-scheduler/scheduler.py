#!/usr/bin/env python3
"""
ETL Scheduler - Scans S3 for new raw data and triggers PySpark jobs
"""
import json
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL', 'http://localstack:4566')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
RAW_BUCKET = os.getenv('RAW_BUCKET', 'md-raw-logs')
TRANSFORMED_LOGS_BUCKET = os.getenv('TRANSFORMED_LOGS_BUCKET', 'md-transformed-logs')
TRANSFORMED_METRICS_BUCKET = os.getenv('TRANSFORMED_METRICS_BUCKET', 'md-transformed-metrics')
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '300'))  # 5 minutes
STATE_FILE = os.getenv('STATE_FILE', '/app/state/processing_state.json')
SPARK_SCRIPT_PATH = os.getenv('SPARK_SCRIPT_PATH', '/app/spark-jobs')

# Initialize S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=AWS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

class ProcessingState:
    """Manage processing state"""
    
    def __init__(self, state_file):
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self):
        """Load state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}, creating new")
        
        return {
            'processed_partitions': [],
            'last_scan': None,
            'stats': {
                'total_processed': 0,
                'total_failed': 0,
                'last_success': None
            }
        }
    
    def _save_state(self):
        """Save state to file"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def is_processed(self, partition_key):
        """Check if partition already processed"""
        return partition_key in self.state['processed_partitions']
    
    def mark_processed(self, partition_key, success=True):
        """Mark partition as processed"""
        if partition_key not in self.state['processed_partitions']:
            self.state['processed_partitions'].append(partition_key)
        
        if success:
            self.state['stats']['total_processed'] += 1
            self.state['stats']['last_success'] = datetime.utcnow().isoformat()
        else:
            self.state['stats']['total_failed'] += 1
        
        self.state['last_scan'] = datetime.utcnow().isoformat()
        self._save_state()
    
    def get_stats(self):
        """Get processing statistics"""
        return self.state['stats']


class ETLScheduler:
    """Main scheduler class"""
    
    def __init__(self):
        self.state = ProcessingState(STATE_FILE)
        self.running = True
    
    def scan_raw_bucket(self):
        """Scan S3 raw bucket for new partitions"""
        logger.info(f"📡 Scanning bucket: {RAW_BUCKET}")
        
        partitions = []
        
        try:
            # List all objects in bucket
            paginator = s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=RAW_BUCKET)
            
            for page in page_iterator:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Parse partition from key
                    # Format: service=X/year=Y/month=M/day=D/hour=H/part-xxx.jsonl
                    if key.endswith('.jsonl'):
                        partition = self._extract_partition(key)
                        if partition and not self.state.is_processed(partition):
                            partitions.append(partition)
            
            # Remove duplicates
            partitions = list(set(partitions))
            
            if partitions:
                logger.info(f"✨ Found {len(partitions)} new partitions to process")
            else:
                logger.info("✅ No new partitions found")
            
            return partitions
        
        except ClientError as e:
            logger.error(f"❌ Error scanning bucket: {e}")
            return []
    
    def _extract_partition(self, s3_key):
        """Extract partition key from S3 object key"""
        # Example: service=api-gateway/year=2025/month=11/day=09/hour=14/part-abc.jsonl
        # Return: service=api-gateway/year=2025/month=11/day=09/hour=14
        
        parts = s3_key.split('/')
        if len(parts) >= 5:
            # Join service through hour
            partition = '/'.join(parts[:-1])
            return partition
        return None
    
    def trigger_spark_job(self, job_name, partition):
        """Trigger PySpark job for partition via docker exec"""
        logger.info(f"🚀 Triggering job: {job_name} for partition: {partition}")
        
        script_path = os.path.join(SPARK_SCRIPT_PATH, f"{job_name}.py")
        
        if not os.path.exists(script_path):
            logger.error(f"❌ Script not found: {script_path}")
            return False
        
        # Execute spark-submit inside etl-spark-worker container
        cmd = [
            'docker', 'exec', 'etl-spark-worker',
            'spark-submit',
            '--master', 'local[*]',
            '--driver-memory', '2g',
            '--executor-memory', '2g',
            '--jars', '/opt/spark/jars/hadoop-aws-3.3.4.jar,/opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar',
            '--conf', f'spark.hadoop.fs.s3a.endpoint={AWS_ENDPOINT_URL}',
            '--conf', 'spark.hadoop.fs.s3a.access.key=test',
            '--conf', 'spark.hadoop.fs.s3a.secret.key=test',
            '--conf', 'spark.hadoop.fs.s3a.path.style.access=true',
            '--conf', 'spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem',
            f'/app/spark-jobs/{job_name}.py',
            '--raw-bucket', RAW_BUCKET,
            '--transformed-bucket', TRANSFORMED_LOGS_BUCKET,
            '--partition', partition
        ]
        
        try:
            logger.info(f"📝 Executing job in spark-worker container")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Job completed successfully: {job_name}")
                if result.stdout:
                    logger.info(f"Output: {result.stdout[-500:]}")  # Last 500 chars
                return True
            else:
                logger.error(f"❌ Job failed: {job_name}")
                if result.stderr:
                    logger.error(f"Error: {result.stderr[-500:]}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ Job timed out: {job_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Error executing job: {e}")
            return False
    
    def process_partition(self, partition):
        """Process a single partition"""
        logger.info(f"🔄 Processing partition: {partition}")
        
        # Run logs processing job
        success = self.trigger_spark_job('logs_processing', partition)
        
        # Mark as processed
        self.state.mark_processed(partition, success)
        
        if success:
            logger.info(f"✅ Successfully processed: {partition}")
        else:
            logger.warning(f"⚠️ Failed to process: {partition}")
        
        return success
    
    def run(self):
        """Main scheduler loop"""
        logger.info("🚀 ETL Scheduler started")
        logger.info(f"📊 Configuration:")
        logger.info(f"   - Raw bucket: {RAW_BUCKET}")
        logger.info(f"   - Transformed bucket: {TRANSFORMED_LOGS_BUCKET}")
        logger.info(f"   - Scan interval: {SCAN_INTERVAL}s")
        logger.info(f"   - State file: {STATE_FILE}")
        
        while self.running:
            try:
                # Scan for new partitions
                partitions = self.scan_raw_bucket()
                
                # Process each partition
                for partition in partitions:
                    self.process_partition(partition)
                
                # Display stats
                stats = self.state.get_stats()
                logger.info(f"📈 Stats: Processed={stats['total_processed']}, Failed={stats['total_failed']}")
                
                # Sleep
                logger.info(f"💤 Sleeping for {SCAN_INTERVAL} seconds...")
                time.sleep(SCAN_INTERVAL)
            
            except KeyboardInterrupt:
                logger.info("⚠️ Received interrupt signal, shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                time.sleep(60)  # Sleep 1 minute on error
        
        logger.info("👋 ETL Scheduler stopped")


if __name__ == '__main__':
    scheduler = ETLScheduler()
    scheduler.run()
