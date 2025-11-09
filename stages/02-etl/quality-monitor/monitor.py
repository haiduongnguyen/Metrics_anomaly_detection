#!/usr/bin/env python3
"""
Data Quality Monitor
Tracks ETL job quality metrics and generates reports
"""
import json
import os
import time
import logging
from datetime import datetime
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL', 'http://localstack:4566')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
RAW_BUCKET = os.getenv('RAW_BUCKET', 'md-raw-logs')
TRANSFORMED_BUCKET = os.getenv('TRANSFORMED_LOGS_BUCKET', 'md-transformed-logs')
METRICS_FILE = os.getenv('METRICS_FILE', '/app/state/quality_metrics.json')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))  # 5 minutes

# Initialize S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=AWS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

class QualityMonitor:
    """Monitor data quality"""
    
    def __init__(self):
        self.metrics = self._load_metrics()
    
    def _load_metrics(self):
        """Load metrics from file"""
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metrics: {e}")
        
        return {
            'last_check': None,
            'raw_objects': 0,
            'transformed_objects': 0,
            'raw_size_bytes': 0,
            'transformed_size_bytes': 0,
            'compression_ratio': 0.0,
            'quality_score': 0.0,
            'checks': []
        }
    
    def _save_metrics(self):
        """Save metrics to file"""
        try:
            os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
            with open(METRICS_FILE, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def count_objects(self, bucket):
        """Count objects and total size in bucket"""
        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=bucket)
            
            total_objects = 0
            total_size = 0
            
            for page in page_iterator:
                if 'Contents' in page:
                    total_objects += len(page['Contents'])
                    total_size += sum(obj['Size'] for obj in page['Contents'])
            
            return total_objects, total_size
        
        except ClientError as e:
            logger.error(f"Error counting objects in {bucket}: {e}")
            return 0, 0
    
    def calculate_quality_score(self):
        """Calculate overall quality score"""
        # Simple scoring: ratio of transformed to raw
        if self.metrics['raw_objects'] == 0:
            return 0.0
        
        processing_rate = min(1.0, self.metrics['transformed_objects'] / max(1, self.metrics['raw_objects']))
        
        # Score based on compression ratio (good if > 3x)
        compression_score = min(1.0, self.metrics['compression_ratio'] / 5.0) if self.metrics['compression_ratio'] > 0 else 0.5
        
        # Weighted average
        quality_score = (processing_rate * 0.7 + compression_score * 0.3) * 100
        
        return round(quality_score, 2)
    
    def check_quality(self):
        """Perform quality check"""
        logger.info("🔍 Checking data quality...")
        
        # Count raw objects
        raw_count, raw_size = self.count_objects(RAW_BUCKET)
        logger.info(f"   Raw: {raw_count} objects, {raw_size/1024/1024:.2f} MB")
        
        # Count transformed objects
        transformed_count, transformed_size = self.count_objects(TRANSFORMED_BUCKET)
        logger.info(f"   Transformed: {transformed_count} objects, {transformed_size/1024/1024:.2f} MB")
        
        # Calculate compression ratio
        compression_ratio = 0.0
        if transformed_size > 0:
            compression_ratio = raw_size / transformed_size
        
        # Update metrics
        self.metrics['last_check'] = datetime.utcnow().isoformat()
        self.metrics['raw_objects'] = raw_count
        self.metrics['transformed_objects'] = transformed_count
        self.metrics['raw_size_bytes'] = raw_size
        self.metrics['transformed_size_bytes'] = transformed_size
        self.metrics['compression_ratio'] = round(compression_ratio, 2)
        self.metrics['quality_score'] = self.calculate_quality_score()
        
        # Add to checks history
        check_record = {
            'timestamp': self.metrics['last_check'],
            'raw_objects': raw_count,
            'transformed_objects': transformed_count,
            'quality_score': self.metrics['quality_score']
        }
        
        self.metrics['checks'].append(check_record)
        
        # Keep only last 100 checks
        if len(self.metrics['checks']) > 100:
            self.metrics['checks'] = self.metrics['checks'][-100:]
        
        # Save metrics
        self._save_metrics()
        
        # Display summary
        logger.info(f"📊 Quality Score: {self.metrics['quality_score']}%")
        logger.info(f"🗜️ Compression Ratio: {compression_ratio:.2f}x")
        
        return self.metrics
    
    def run(self):
        """Main monitor loop"""
        logger.info("🚀 Data Quality Monitor started")
        logger.info(f"📊 Check interval: {CHECK_INTERVAL}s")
        
        while True:
            try:
                self.check_quality()
                logger.info(f"💤 Sleeping for {CHECK_INTERVAL} seconds...")
                time.sleep(CHECK_INTERVAL)
            
            except KeyboardInterrupt:
                logger.info("⚠️ Shutting down...")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitor loop: {e}", exc_info=True)
                time.sleep(60)
        
        logger.info("👋 Quality Monitor stopped")

if __name__ == '__main__':
    monitor = QualityMonitor()
    monitor.run()
