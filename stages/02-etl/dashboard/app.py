#!/usr/bin/env python3
"""
Stage 02 Dashboard - ETL Processing Monitoring
Streamlit dashboard for ETL job monitoring
"""
import streamlit as st
import json
import os
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Stage 02 - ETL Processing",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL', 'http://localstack:4566')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
RAW_BUCKET = 'md-raw-logs'
TRANSFORMED_BUCKET = 'md-transformed-logs'
METRICS_BUCKET = 'md-transformed-metrics'
STATE_FILE = '/app/state/processing_state.json'
QUALITY_FILE = '/app/state/quality_metrics.json'

# Initialize S3 client
@st.cache_resource
def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )

s3_client = get_s3_client()

# Helper functions
def load_json_file(filepath):
    """Load JSON file"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading {filepath}: {e}")
    return None

def count_s3_objects(bucket):
    """Count objects in S3 bucket"""
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket)
        
        total_count = 0
        total_size = 0
        
        for page in page_iterator:
            if 'Contents' in page:
                total_count += len(page['Contents'])
                total_size += sum(obj['Size'] for obj in page['Contents'])
        
        return total_count, total_size
    except ClientError:
        return 0, 0

def list_s3_objects(bucket, max_keys=100):
    """List objects in S3 bucket"""
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            MaxKeys=max_keys
        )
        
        if 'Contents' in response:
            return response['Contents']
        return []
    except ClientError:
        return []

# Main dashboard
st.title("🔄 Stage 02 - ETL Processing Dashboard")
st.markdown("Real-time monitoring of ETL jobs, data quality, and processing statistics")

# Auto-refresh
if st.sidebar.checkbox("Auto-refresh (10s)", value=True):
    st_autorefresh = st.empty()
    import time
    time.sleep(10)
    st.rerun()

# Refresh button
if st.sidebar.button("🔄 Refresh Now"):
    st.rerun()

# Sidebar - System Status
st.sidebar.header("📊 System Status")

# Load processing state
processing_state = load_json_file(STATE_FILE)
quality_metrics = load_json_file(QUALITY_FILE)

if processing_state:
    st.sidebar.metric(
        "Processed Partitions", 
        processing_state['stats']['total_processed']
    )
    st.sidebar.metric(
        "Failed Jobs", 
        processing_state['stats']['total_failed']
    )
    
    if processing_state['stats']['last_success']:
        last_success = datetime.fromisoformat(processing_state['stats']['last_success'])
        st.sidebar.info(f"Last success: {last_success.strftime('%H:%M:%S')}")

if quality_metrics:
    score = quality_metrics.get('quality_score', 0)
    
    if score >= 90:
        st.sidebar.success(f"✅ Quality Score: {score}%")
    elif score >= 75:
        st.sidebar.warning(f"⚠️ Quality Score: {score}%")
    else:
        st.sidebar.error(f"❌ Quality Score: {score}%")

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview", 
    "🗄️ Data Browser", 
    "📈 Quality Metrics", 
    "⚙️ Job History"
])

# Tab 1: Overview
with tab1:
    st.header("Pipeline Overview")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    raw_count, raw_size = count_s3_objects(RAW_BUCKET)
    transformed_count, transformed_size = count_s3_objects(TRANSFORMED_BUCKET)
    
    with col1:
        st.metric(
            "Raw Objects",
            f"{raw_count:,}",
            delta=f"{raw_size/1024/1024:.1f} MB"
        )
    
    with col2:
        st.metric(
            "Transformed Objects",
            f"{transformed_count:,}",
            delta=f"{transformed_size/1024/1024:.1f} MB"
        )
    
    with col3:
        compression_ratio = 0
        if transformed_size > 0:
            compression_ratio = raw_size / transformed_size
        st.metric(
            "Compression Ratio",
            f"{compression_ratio:.2f}x",
            delta="Good" if compression_ratio > 3 else "Normal"
        )
    
    with col4:
        processing_rate = 0
        if raw_count > 0:
            processing_rate = (transformed_count / raw_count) * 100
        st.metric(
            "Processing Rate",
            f"{processing_rate:.1f}%"
        )
    
    # ETL Pipeline Diagram
    st.subheader("ETL Pipeline Flow")
    
    st.markdown("""
    ```
    Stage 01: Raw Data (JSONL)
            ↓
    ETL Scheduler (Scan & Trigger)
            ↓
    PySpark Jobs (Transform & Clean)
            ↓
    Stage 02: Transformed Data (Parquet)
    ```
    """)
    
    # Recent activity
    if processing_state and processing_state.get('processed_partitions'):
        st.subheader("Recent Processed Partitions")
        recent = processing_state['processed_partitions'][-10:]
        for partition in reversed(recent):
            st.text(f"✅ {partition}")

# Tab 2: Data Browser
with tab2:
    st.header("S3 Data Browser")
    
    bucket_choice = st.selectbox(
        "Select Bucket",
        [RAW_BUCKET, TRANSFORMED_BUCKET, METRICS_BUCKET]
    )
    
    objects = list_s3_objects(bucket_choice, max_keys=50)
    
    if objects:
        st.success(f"Found {len(objects)} objects")
        
        # Create dataframe
        df = pd.DataFrame([
            {
                'Key': obj['Key'],
                'Size (KB)': obj['Size'] / 1024,
                'Last Modified': obj['LastModified']
            }
            for obj in objects
        ])
        
        st.dataframe(df, use_container_width=True, height=400)
        
        # Object details
        selected_key = st.selectbox("Select object to view details", df['Key'].tolist())
        
        if selected_key:
            st.code(selected_key, language="text")
            
            obj_detail = next((o for o in objects if o['Key'] == selected_key), None)
            if obj_detail:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Size", f"{obj_detail['Size']/1024:.2f} KB")
                with col2:
                    st.metric("Last Modified", obj_detail['LastModified'].strftime('%Y-%m-%d %H:%M:%S'))
    else:
        st.info("No objects found in bucket")

# Tab 3: Quality Metrics
with tab3:
    st.header("Data Quality Metrics")
    
    if quality_metrics:
        # Quality score gauge
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = quality_metrics.get('quality_score', 0),
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Overall Quality Score"},
            delta = {'reference': 90},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 75], 'color': "yellow"},
                    {'range': [75, 90], 'color': "orange"},
                    {'range': [90, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 95
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Metrics table
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Storage Metrics")
            st.metric("Raw Size", f"{quality_metrics['raw_size_bytes']/1024/1024:.2f} MB")
            st.metric("Transformed Size", f"{quality_metrics['transformed_size_bytes']/1024/1024:.2f} MB")
            st.metric("Compression Ratio", f"{quality_metrics['compression_ratio']:.2f}x")
        
        with col2:
            st.subheader("Object Counts")
            st.metric("Raw Objects", quality_metrics['raw_objects'])
            st.metric("Transformed Objects", quality_metrics['transformed_objects'])
            
            if quality_metrics.get('last_check'):
                last_check = datetime.fromisoformat(quality_metrics['last_check'])
                st.info(f"Last check: {last_check.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Quality history chart
        if quality_metrics.get('checks'):
            st.subheader("Quality Score History")
            
            checks_df = pd.DataFrame(quality_metrics['checks'])
            checks_df['timestamp'] = pd.to_datetime(checks_df['timestamp'])
            
            fig = px.line(
                checks_df,
                x='timestamp',
                y='quality_score',
                title='Quality Score Over Time',
                labels={'quality_score': 'Quality Score (%)', 'timestamp': 'Time'}
            )
            fig.add_hline(y=90, line_dash="dash", line_color="green", annotation_text="Target: 90%")
            
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.warning("Quality metrics not available yet. Wait for quality monitor to run.")

# Tab 4: Job History
with tab4:
    st.header("ETL Job History")
    
    if processing_state:
        stats = processing_state['stats']
        
        # Summary cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Processed", stats['total_processed'])
        with col2:
            st.metric("Total Failed", stats['total_failed'])
        with col3:
            success_rate = 0
            total = stats['total_processed'] + stats['total_failed']
            if total > 0:
                success_rate = (stats['total_processed'] / total) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Processed partitions list
        st.subheader("Processed Partitions")
        
        if processing_state.get('processed_partitions'):
            partitions_df = pd.DataFrame([
                {'Partition': p, 'Status': '✅ Completed'}
                for p in processing_state['processed_partitions'][-50:]
            ])
            
            st.dataframe(partitions_df, use_container_width=True, height=400)
        else:
            st.info("No processed partitions yet")
    
    else:
        st.warning("Processing state not available")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Stage 02 - ETL Processing Layer")
st.sidebar.caption(f"Powered by PySpark & Streamlit")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
