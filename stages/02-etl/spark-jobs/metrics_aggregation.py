#!/usr/bin/env python3
"""
PySpark ETL Job - Metrics Aggregation
Aggregates metrics with time windows
"""
import argparse
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, window, avg, min as spark_min, max as spark_max, 
    stddev, count, percentile_approx, from_unixtime
)
from pyspark.sql.types import IntegerType

def create_spark_session(app_name="MetricsAggregation"):
    """Create Spark session"""
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark

def aggregate_metrics(df, window_duration):
    """Aggregate metrics by time window"""
    print(f"📊 Aggregating with window: {window_duration}")
    
    # Filter records with numeric metrics
    metrics_df = df.filter(
        col("latency_ms").isNotNull() | col("response_time").isNotNull()
    )
    
    if metrics_df.count() == 0:
        print("⚠️ No metric records found")
        return None
    
    # Aggregate by service and time window
    agg_df = metrics_df.groupBy(
        "service",
        window(col("timestamp"), window_duration)
    ).agg(
        count("*").alias("count"),
        avg("latency_ms").alias("latency_avg"),
        spark_min("latency_ms").alias("latency_min"),
        spark_max("latency_ms").alias("latency_max"),
        percentile_approx("latency_ms", 0.5).alias("latency_p50"),
        percentile_approx("latency_ms", 0.95).alias("latency_p95"),
        percentile_approx("latency_ms", 0.99).alias("latency_p99"),
        stddev("latency_ms").alias("latency_stddev"),
        avg("response_time").alias("response_time_avg"),
        avg("anomaly_score").alias("anomaly_score_avg")
    )
    
    # Extract window start/end
    agg_df = agg_df.withColumn("window_start", col("window.start"))
    agg_df = agg_df.withColumn("window_end", col("window.end"))
    agg_df = agg_df.drop("window")
    
    # Add partition columns
    agg_df = agg_df.withColumn("date", 
        from_unixtime(col("window_start").cast("long"), "yyyy-MM-dd")
    )
    
    return agg_df

def write_aggregated(df, output_path, window_name):
    """Write aggregated metrics to Parquet"""
    if df is None:
        return
    
    print(f"💾 Writing {window_name} aggregations to: {output_path}")
    
    df.write \
        .mode("append") \
        .partitionBy("date") \
        .format("parquet") \
        .option("compression", "snappy") \
        .save(f"{output_path}/{window_name}")
    
    print("✅ Write completed")

def main():
    parser = argparse.ArgumentParser(description='Aggregate metrics')
    parser.add_argument('--transformed-logs-bucket', required=True)
    parser.add_argument('--transformed-metrics-bucket', required=True)
    parser.add_argument('--partition-date', required=True, help='Date partition (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🚀 Starting Metrics Aggregation Job")
    print("="*60)
    
    spark = create_spark_session()
    
    input_path = f"s3a://{args.transformed_logs_bucket}/date={args.partition_date}/*/*"
    output_path = f"s3a://{args.transformed_metrics_bucket}/"
    
    try:
        print(f"📖 Reading from: {input_path}")
        df = spark.read.parquet(input_path)
        
        # 1-minute aggregation
        agg_1m = aggregate_metrics(df, "1 minute")
        write_aggregated(agg_1m, output_path, "1minute")
        
        # 5-minute aggregation
        agg_5m = aggregate_metrics(df, "5 minutes")
        write_aggregated(agg_5m, output_path, "5minutes")
        
        # 1-hour aggregation
        agg_1h = aggregate_metrics(df, "1 hour")
        write_aggregated(agg_1h, output_path, "1hour")
        
        print()
        print("✅ Metrics aggregation completed")
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
