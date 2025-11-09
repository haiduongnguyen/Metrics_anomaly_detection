#!/usr/bin/env python3
"""
PySpark ETL Job - Logs Processing
Transforms raw JSONL logs to optimized Parquet format
"""
import argparse
import sys
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, regexp_extract, length, unix_timestamp, from_unixtime,
    to_timestamp, current_timestamp, md5, concat_ws
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType,
    IntegerType, BooleanType, LongType
)

def create_spark_session(app_name="LogsProcessing"):
    """Create Spark session with S3 configuration"""
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.files.maxPartitionBytes", "128MB") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark

def define_raw_schema():
    """Define schema for raw JSONL logs - note: data is nested"""
    # Schema flexible enough to handle nested structure
    return None  # Let Spark infer schema

def validate_data(df):
    """Validate required fields"""
    print("📋 Validating data...")
    
    # Count records
    total_records = df.count()
    print(f"   Total records: {total_records}")
    
    if total_records == 0:
        print("⚠️ No records to process")
        return df
    
    # Check required fields
    required_fields = ['timestamp', 'service', 'level', 'message']
    
    valid_df = df
    for field in required_fields:
        valid_df = valid_df.filter(col(field).isNotNull())
    
    valid_records = valid_df.count()
    invalid_records = total_records - valid_records
    
    print(f"   Valid records: {valid_records}")
    print(f"   Invalid records: {invalid_records}")
    print(f"   Validation rate: {valid_records/total_records*100:.2f}%")
    
    return valid_df

def transform_logs(df):
    """Transform raw logs to target schema"""
    print("🔄 Transforming data...")
    
    # Convert timestamp to proper timestamp type
    df = df.withColumn("timestamp", to_timestamp(col("timestamp")))
    
    # Calculate timestamp_epoch
    df = df.withColumn("timestamp_epoch", unix_timestamp(col("timestamp")))
    
    # Normalize log level
    df = df.withColumn("level", 
        when(col("level").isin("info", "INFO", "Info"), "INFO")
        .when(col("level").isin("warn", "WARN", "Warn", "warning", "WARNING"), "WARN")
        .when(col("level").isin("error", "ERROR", "Error"), "ERROR")
        .when(col("level").isin("debug", "DEBUG", "Debug"), "DEBUG")
        .otherwise("INFO")
    )
    
    # Calculate level_numeric
    df = df.withColumn("level_numeric",
        when(col("level") == "DEBUG", 0)
        .when(col("level") == "INFO", 1)
        .when(col("level") == "WARN", 2)
        .when(col("level") == "ERROR", 3)
        .otherwise(1)
    )
    
    # Clean message
    df = df.withColumn("message_clean", col("message"))
    df = df.withColumn("message_length", length(col("message")))
    
    # Extract error code from message (pattern: ERROR-XXX or ERR-XXX)
    df = df.withColumn("error_code_extracted",
        when(col("error_code").isNotNull(), col("error_code"))
        .otherwise(regexp_extract(col("message"), r"(ERR(?:OR)?-\w+)", 1))
    )
    
    # Extract user_id if not present (pattern: user-XXX or user_XXX)
    df = df.withColumn("user_id_extracted",
        when(col("user_id").isNotNull(), col("user_id"))
        .otherwise(regexp_extract(col("message"), r"(user[-_]\w+)", 1))
    )
    
    # Extract request_id if not present (pattern: req-XXX or request-XXX)
    df = df.withColumn("request_id_extracted",
        when(col("request_id").isNotNull(), col("request_id"))
        .otherwise(regexp_extract(col("message"), r"(req(?:uest)?[-_]\w+)", 1))
    )
    
    # Anomaly flag
    df = df.withColumn("anomaly_flag", 
        when(col("anomaly_score") > 75, True).otherwise(False)
    )
    
    # Select final columns
    transformed_df = df.select(
        col("timestamp"),
        col("timestamp_epoch"),
        col("service"),
        col("level"),
        col("level_numeric"),
        col("message_clean"),
        col("message_length"),
        col("trace_id"),
        col("span_id"),
        col("source"),
        col("log_type"),
        col("anomaly_score"),
        col("anomaly_flag"),
        col("error_code_extracted").alias("error_code"),
        col("user_id_extracted").alias("user_id"),
        col("request_id_extracted").alias("request_id"),
        col("status_code"),
        col("latency_ms"),
        col("response_time")
    )
    
    return transformed_df

def deduplicate(df):
    """Remove duplicate records"""
    print("🔍 Deduplicating...")
    
    initial_count = df.count()
    
    # Create dedup key
    df = df.withColumn("dedup_key", 
        md5(concat_ws("|", col("trace_id"), col("timestamp_epoch")))
    )
    
    # Drop duplicates
    deduped_df = df.dropDuplicates(["dedup_key"])
    
    final_count = deduped_df.count()
    duplicates = initial_count - final_count
    
    print(f"   Initial: {initial_count}")
    print(f"   Duplicates removed: {duplicates}")
    print(f"   Final: {final_count}")
    
    # Drop dedup key
    deduped_df = deduped_df.drop("dedup_key")
    
    return deduped_df

def write_parquet(df, output_path):
    """Write dataframe to Parquet with partitioning"""
    print(f"💾 Writing to: {output_path}")
    
    # Add partition columns
    df = df.withColumn("date", 
        from_unixtime(col("timestamp_epoch"), "yyyy-MM-dd")
    )
    df = df.withColumn("hour", 
        from_unixtime(col("timestamp_epoch"), "HH").cast(IntegerType())
    )
    
    # Write partitioned parquet
    df.write \
        .mode("append") \
        .partitionBy("date", "hour") \
        .format("parquet") \
        .option("compression", "snappy") \
        .save(output_path)
    
    print("✅ Write completed")

def main():
    parser = argparse.ArgumentParser(description='Process raw logs to Parquet')
    parser.add_argument('--raw-bucket', required=True, help='Raw S3 bucket name')
    parser.add_argument('--transformed-bucket', required=True, help='Transformed S3 bucket name')
    parser.add_argument('--partition', required=True, help='Partition path to process')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🚀 Starting Logs Processing Job")
    print("="*60)
    print(f"📂 Raw bucket: {args.raw_bucket}")
    print(f"📂 Transformed bucket: {args.transformed_bucket}")
    print(f"📁 Partition: {args.partition}")
    print()
    
    # Create Spark session
    spark = create_spark_session()
    
    # Define input/output paths
    input_path = f"s3a://{args.raw_bucket}/{args.partition}/*.jsonl"
    output_path = f"s3a://{args.transformed_bucket}/"
    
    try:
        # Read raw data
        print(f"📖 Reading from: {input_path}")
        df = spark.read.json(input_path)
        
        # Flatten nested 'data' column if it exists
        if 'data' in df.columns:
            print("🔄 Flattening nested 'data' structure...")
            # Extract all fields from 'data' column
            data_fields = df.select("data.*").columns
            for field in data_fields:
                df = df.withColumn(f"data_{field}", col(f"data.{field}"))
            
            # Drop original nested column and rename
            df = df.drop("data")
            
            # Rename data_* columns to remove prefix
            for field in data_fields:
                if field != "timestamp":  # Keep outer timestamp
                    df = df.withColumnRenamed(f"data_{field}", field)
                else:
                    df = df.withColumnRenamed(f"data_timestamp", "timestamp_inner")
                    # Use inner timestamp if outer is not useful
                    df = df.withColumn("timestamp", 
                        when(col("timestamp_inner").isNotNull(), col("timestamp_inner"))
                        .otherwise(col("timestamp"))
                    )
                    df = df.drop("timestamp_inner")
        
        # Validate
        df = validate_data(df)
        
        if df.count() == 0:
            print("⚠️ No valid records to process")
            return 0
        
        # Transform
        df = transform_logs(df)
        
        # Deduplicate
        df = deduplicate(df)
        
        # Write
        write_parquet(df, output_path)
        
        print()
        print("="*60)
        print("✅ Job completed successfully")
        print("="*60)
        return 0
    
    except Exception as e:
        print(f"❌ Job failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        spark.stop()

if __name__ == "__main__":
    sys.exit(main())
