"""
Scenario Orchestrator Service
Central coordination service for managing 200 anomaly scenarios
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import httpx
import json
import uuid
from enum import Enum
import random
import math

from infrastructure_scenarios import (
    INFRASTRUCTURE_SCENARIOS,
    get_scenario_by_id,
    get_all_infrastructure_scenarios,
    get_scenarios_by_severity,
    InfraScenarioType
)

app = FastAPI(title="Scenario Orchestrator Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class ScenarioCategory(str, Enum):
    TECHNICAL = "Technical"
    BUSINESS = "Business"
    SECURITY = "Security"

class SeverityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

# Models
class ScenarioConfig(BaseModel):
    scenario_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    duration_seconds: int = 300
    log_rate: int = 100  # logs per second

class Scenario(BaseModel):
    id: str
    name: str
    category: ScenarioCategory
    severity: SeverityLevel
    description: str
    default_params: Dict[str, Any]

class Execution(BaseModel):
    id: str
    scenario_id: str
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    config: ScenarioConfig
    logs_generated: int = 0
    error_message: Optional[str] = None
    is_manual: bool = False
    anomaly_type: Optional[str] = None

class ContinuousConfig(BaseModel):
    enabled: bool = False
    normal_log_rate: int = 100  # logs per second for normal traffic
    anomaly_frequency: int = 5000  # 1 anomaly per N normal logs (realistic: 1/5000 = 0.02%)
    anomaly_duration: int = 30  # seconds per anomaly
    log_types: List[str] = ["application", "security", "transaction"]

# In-memory storage
scenarios_db: Dict[str, Scenario] = {}
executions_db: Dict[str, Execution] = {}

# Global continuous generation state
continuous_state = {
    "enabled": False,
    "config": ContinuousConfig(),
    "normal_logs_generated": 0,
    "anomalies_injected": 0,
    "last_anomaly_at": None,
    "current_anomaly": None
}

# Service URLs
PATTERN_GENERATOR_URL = "http://pattern-generator:8001"
STATE_MANAGER_URL = "http://state-manager:8003"
LOG_SYNTHESIS_URL = "http://log-synthesis:8002"

# Realistic log type frequency distribution
LOG_TYPE_FREQUENCIES = {
    # Infrastructure & System Logs (40% of total traffic)
    "server_log": 15.0,
    "container_log": 12.0,
    "network_log": 5.0,
    "storage_log": 3.0,
    "cdn_log": 2.0,
    "dns_log": 1.5,
    "load_balancer_log": 1.0,
    "firewall_log": 0.5,
    "vpn_log": 0.3,
    
    # Application Layer Logs (25% of total traffic)
    "application_log": 10.0,
    "api_gateway_log": 8.0,
    "microservice_log": 4.0,
    "middleware_log": 1.5,
    "cache_log": 1.0,
    "message_queue_log": 0.5,
    
    # Database & Data Store Logs (15% of total traffic)
    "database_query_log": 6.0,
    "database_transaction_log": 4.0,
    "nosql_log": 2.0,
    "redis_log": 1.5,
    "elasticsearch_log": 0.8,
    "database_replication_log": 0.3,
    "database_backup_log": 0.2,
    "data_migration_log": 0.2,
    
    # Security & Authentication Logs (10% of total traffic)
    "authentication_log": 4.0,
    "authorization_log": 2.5,
    "waf_log": 1.5,
    "ids_ips_log": 1.0,
    "dlp_log": 0.5,
    "encryption_log": 0.3,
    "certificate_log": 0.2,
    
    # Business Transaction Logs (5% of total traffic)
    "payment_transaction_log": 2.0,
    "fund_transfer_log": 1.5,
    "settlement_log": 0.8,
    "reconciliation_log": 0.5,
    "clearing_log": 0.2,
    
    # Fraud Detection & AML Logs (2% of total traffic)
    "fraud_detection_log": 1.0,
    "aml_screening_log": 0.7,
    "risk_assessment_log": 0.3,
    
    # User Behavior & Analytics Logs (1.5% of total traffic)
    "user_session_log": 0.5,
    "clickstream_log": 0.3,
    "user_navigation_log": 0.3,
    "search_log": 0.2,
    "conversion_log": 0.1,
    "ab_test_log": 0.1,
    
    # Compliance & Audit Logs (0.8% of total traffic)
    "audit_trail_log": 0.5,
    "regulatory_report_log": 0.2,
    "compliance_check_log": 0.1,
    
    # External Integration Logs (0.5% of total traffic)
    "third_party_api_log": 0.3,
    "webhook_log": 0.1,
    "partner_integration_log": 0.1,
    
    # Monitoring & Observability Logs (0.15% of total traffic)
    "metrics_log": 0.08,
    "distributed_trace_log": 0.05,
    "alert_log": 0.02,
    
    # Business Intelligence & Analytics Logs (0.03% of total traffic)
    "bi_report_log": 0.02,
    "data_warehouse_log": 0.01,
    
    # Specialized Logs (0.02% of total traffic)
    "ml_model_log": 0.01,
    "blockchain_log": 0.01
}

def select_realistic_log_type() -> str:
    """Select a log type based on realistic frequency distribution"""
    log_types = list(LOG_TYPE_FREQUENCIES.keys())
    weights = list(LOG_TYPE_FREQUENCIES.values())
    return random.choices(log_types, weights=weights, k=1)[0]

# Initialize sample scenarios
def init_scenarios():
    """Initialize 200 anomaly scenarios"""
    categories = [
        (ScenarioCategory.TECHNICAL, 90),
        (ScenarioCategory.BUSINESS, 90),
        (ScenarioCategory.SECURITY, 20)
    ]
    
    scenario_id = 1
    for category, count in categories:
        for i in range(count):
            severity = list(SeverityLevel)[scenario_id % 4]
            scenario = Scenario(
                id=f"{category.value[:3].upper()}_{scenario_id:03d}",
                name=f"{category.value} Anomaly {i+1}",
                category=category,
                severity=severity,
                description=f"Simulates {category.value.lower()} anomaly pattern {i+1}",
                default_params={
                    "spike_percentage": 85 if category == ScenarioCategory.TECHNICAL else 0,
                    "duration_minutes": 5,
                    "affected_entities": 3,
                    "pattern": "gradual_increase"
                }
            )
            scenarios_db[scenario.id] = scenario
            scenario_id += 1

@app.on_event("startup")
async def startup_event():
    init_scenarios()
    print(f"Initialized {len(scenarios_db)} general scenarios")
    print(f"Loaded {len(INFRASTRUCTURE_SCENARIOS)} infrastructure scenarios")
    
    print("[v0] Auto-starting continuous log generation...")
    continuous_state["enabled"] = True
    continuous_state["config"] = ContinuousConfig(
        enabled=True,
        normal_log_rate=100,
        anomaly_frequency=5000,
        anomaly_duration=30,
        log_types=list(LOG_TYPE_FREQUENCIES.keys())
    )
    continuous_state["normal_logs_generated"] = 0
    continuous_state["anomalies_injected"] = 0
    continuous_state["last_anomaly_at"] = None
    continuous_state["current_anomaly"] = None
    
    # Start continuous generation in background
    asyncio.create_task(run_continuous_generation())
    print("[v0] Continuous generation started automatically!")

@app.get("/")
async def root():
    """Serve the web UI"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Scenario Orchestrator</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            /* Complete UI redesign with modern, soft, harmonious colors */
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            :root {
                --primary: #6366f1;
                --primary-light: #818cf8;
                --primary-dark: #4f46e5;
                --secondary: #8b5cf6;
                --accent: #ec4899;
                --success: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
                --bg-primary: #f8fafc;
                --bg-secondary: #ffffff;
                --bg-card: #ffffff;
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --text-muted: #94a3b8;
                --border: #e2e8f0;
                --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 2rem;
                color: var(--text-primary);
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .header {
                background: var(--bg-card);
                border-radius: 16px;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: var(--shadow-lg);
                backdrop-filter: blur(10px);
            }
            
            .header h1 {
                font-size: 2rem;
                font-weight: 700;
                background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 0.5rem;
            }
            
            .header p {
                color: var(--text-secondary);
                font-size: 0.95rem;
            }
            
            .card {
                background: var(--bg-card);
                border-radius: 16px;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: var(--shadow-lg);
                border: 1px solid var(--border);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-xl);
            }
            
            .card-header {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 1.5rem;
                padding-bottom: 1rem;
                border-bottom: 2px solid var(--border);
            }
            
            .card-header h2 {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--text-primary);
            }
            
            .card-header .icon {
                font-size: 1.75rem;
            }
            
            .card-description {
                color: var(--text-secondary);
                font-size: 0.9rem;
                margin-bottom: 1.5rem;
            }
            
            /* Stats Grid */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin-bottom: 2rem;
            }
            
            .stat-card {
                background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: var(--shadow);
                transition: transform 0.2s;
            }
            
            .stat-card:hover {
                transform: scale(1.05);
            }
            
            .stat-value {
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
            }
            
            .stat-label {
                font-size: 0.85rem;
                opacity: 0.9;
                font-weight: 500;
            }
            
            /* Trigger Grid */
            .trigger-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 1rem;
                margin-bottom: 2rem;
            }
            
            .trigger-btn {
                background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 1.5rem;
                cursor: pointer;
                text-align: left;
                transition: all 0.3s;
                box-shadow: var(--shadow);
                position: relative;
                overflow: hidden;
            }
            
            .trigger-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
                opacity: 0;
                transition: opacity 0.3s;
            }
            
            .trigger-btn:hover::before {
                opacity: 1;
            }
            
            .trigger-btn:hover {
                transform: translateY(-4px);
                box-shadow: var(--shadow-xl);
            }
            
            .trigger-btn:active {
                transform: translateY(-2px);
            }
            
            .trigger-btn .title {
                font-weight: 600;
                font-size: 1rem;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .trigger-btn .desc {
                font-size: 0.85rem;
                opacity: 0.9;
                line-height: 1.4;
            }
            
            .severity-critical {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            }
            
            .severity-high {
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            }
            
            .severity-medium {
                background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            }
            
            /* Custom Form */
            .custom-form {
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                padding: 2rem;
                border-radius: 12px;
                border: 2px solid var(--border);
            }
            
            .custom-form h3 {
                margin-bottom: 1.5rem;
                color: var(--text-primary);
                font-size: 1.25rem;
                font-weight: 600;
            }
            
            .form-grid {
                display: grid;
                grid-template-columns: 2fr 1fr 1fr auto;
                gap: 1rem;
                align-items: end;
            }
            
            .form-group {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .form-group label {
                font-weight: 600;
                color: var(--text-primary);
                font-size: 0.9rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .form-group label .hint {
                font-size: 0.75rem;
                color: var(--text-muted);
                font-weight: 400;
            }
            
            select, input[type="number"] {
                padding: 0.75rem;
                border: 2px solid var(--border);
                border-radius: 8px;
                font-size: 0.95rem;
                transition: all 0.2s;
                background: white;
                color: var(--text-primary);
            }
            
            select:focus, input[type="number"]:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }
            
            .helper-text {
                font-size: 0.75rem;
                color: var(--text-muted);
                margin-top: 0.25rem;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
                color: white;
                border: none;
                padding: 0.875rem 2rem;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: var(--shadow);
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-lg);
            }
            
            .btn-primary:active {
                transform: translateY(0);
            }
            
            .info-box {
                background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                padding: 1rem;
                border-radius: 8px;
                font-size: 0.85rem;
                color: #1e40af;
                margin-top: 1rem;
                border-left: 4px solid #3b82f6;
            }
            
            .info-box strong {
                font-weight: 600;
            }
            
            /* Config Controls */
            .config-row {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1rem;
                padding: 1rem;
                background: var(--bg-primary);
                border-radius: 8px;
            }
            
            .config-row label {
                min-width: 220px;
                font-weight: 600;
                color: var(--text-primary);
                font-size: 0.9rem;
            }
            
            .config-row input {
                flex: 1;
                max-width: 200px;
            }
            
            .config-row .hint {
                color: var(--text-muted);
                font-size: 0.85rem;
            }
            
            .toggle-btn {
                width: 100%;
                padding: 1.25rem 2rem;
                font-size: 1.1rem;
                font-weight: 600;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s;
                background: linear-gradient(135deg, var(--success) 0%, #059669 100%);
                color: white;
                box-shadow: var(--shadow-lg);
            }
            
            .toggle-btn:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-xl);
            }
            
            .toggle-btn.active {
                background: linear-gradient(135deg, var(--danger) 0%, #dc2626 100%);
            }
            
            /* Manual Incidents Section */
            .manual-incidents-section {
                padding: 1rem 0;
            }
            
            .section-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1.5rem;
                padding-bottom: 1rem;
                border-bottom: 2px solid var(--border);
            }
            
            .section-header h3 {
                font-size: 1.25rem;
                font-weight: 600;
                color: var(--text-primary);
                margin: 0;
            }
            
            .btn-refresh {
                background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%);
                color: white;
                border: none;
                padding: 0.625rem 1.25rem;
                border-radius: 8px;
                font-size: 0.9rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                box-shadow: var(--shadow-sm);
            }
            
            .btn-refresh:hover {
                transform: translateY(-1px);
                box-shadow: var(--shadow);
            }
            
            .incidents-list {
                min-height: 200px;
                max-height: 400px;
                overflow-y: auto;
                border: 2px solid var(--border);
                border-radius: 12px;
                background: var(--bg-primary);
            }
            
            .loading-indicator {
                text-align: center;
                padding: 3rem 1rem;
                color: var(--text-muted);
                font-style: italic;
            }
            
            .empty-state {
                text-align: center;
                padding: 3rem 1rem;
                color: var(--text-muted);
            }
            
            .empty-state .icon {
                font-size: 3rem;
                margin-bottom: 1rem;
                opacity: 0.5;
            }
            
            .incident-card {
                background: white;
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 0.75rem;
                transition: all 0.2s;
                position: relative;
            }
            
            .incident-card:hover {
                transform: translateX(4px);
                box-shadow: var(--shadow);
                border-color: var(--primary);
            }
            
            .incident-card.running {
                border-left: 4px solid var(--warning);
                background: linear-gradient(135deg, #fef3c7 0%, #fef9c3 100%);
            }
            
            .incident-card.completed {
                border-left: 4px solid var(--success);
                background: linear-gradient(135deg, #d1fae5 0%, #ecfdf5 100%);
            }
            
            .incident-card.failed {
                border-left: 4px solid var(--danger);
                background: linear-gradient(135deg, #fee2e2 0%, #fef2f2 100%);
            }
            
            .incident-card.manual {
                border-left: 4px solid var(--primary);
                background: linear-gradient(135deg, #e0e7ff 0%, #eef2ff 100%);
            }
            
            .incident-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 0.75rem;
            }
            
            .incident-title {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-weight: 600;
                color: var(--text-primary);
            }
            
            .incident-badge {
                background: var(--primary);
                color: white;
                font-size: 0.7rem;
                font-weight: 600;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .incident-status {
                display: flex;
                align-items: center;
                gap: 0.25rem;
                font-size: 0.85rem;
                font-weight: 500;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
            }
            
            .status-running {
                background: var(--warning);
                color: white;
            }
            
            .status-completed {
                background: var(--success);
                color: white;
            }
            
            .status-failed {
                background: var(--danger);
                color: white;
            }
            
            .incident-details {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 0.5rem;
                font-size: 0.85rem;
                color: var(--text-secondary);
                margin-bottom: 0.5rem;
            }
            
            .incident-detail {
                display: flex;
                gap: 0.25rem;
            }
            
            .incident-detail .label {
                font-weight: 600;
                color: var(--text-muted);
            }
            
            .incident-timestamp {
                font-size: 0.75rem;
                color: var(--text-muted);
                margin-top: 0.5rem;
            }
            
            /* Custom Form Layout Fix */
            .custom-form-layout {
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                padding: 2rem;
                border-radius: 12px;
                border: 2px solid var(--border);
            }
            
            .form-row {
                display: grid;
                grid-template-columns: 2fr 1fr 1fr auto;
                gap: 1rem;
                align-items: end;
                margin-bottom: 1.5rem;
            }
            
            @media (max-width: 768px) {
                body {
                    padding: 1rem;
                }
                
                .form-row {
                    grid-template-columns: 1fr;
                }
                
                .stats-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .trigger-grid {
                    grid-template-columns: 1fr;
                }
                
                .section-header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 1rem;
                }
                
                .incident-details {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Scenario Orchestrator</h1>
                <p>Hệ thống mô phỏng và quản lý các kịch bản bất thường cho môi trường ngân hàng</p>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="icon">🖐️</span>
                    <h2>Sự Cố Thủ Công</h2>
                </div>
                <p class="card-description">Quản lý các sự cố bạn đã tạo thủ công theo dõi và phân tích hiệu quả</p>
                
                <div class="manual-incidents-section">
                    <div class="section-header">
                        <h3>📋 Lịch Sử Sự Cố Thủ Công</h3>
                        <button class="btn-refresh" onclick="loadManualIncidents()">🔄 Làm mới</button>
                    </div>
                    
                    <div class="incidents-list" id="manualIncidentsList">
                        <div class="loading-indicator">Đang tải dữ liệu...</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="icon">🚨</span>
                    <h2>Tạo Sự Cố Bất Thường</h2>
                </div>
                <p class="card-description">Nhấn vào nút bên dưới để tạo ngay một sự cố bất thường cụ thể với các thông số đã được cấu hình sẵn</p>
                
                <div class="trigger-grid">
                    <button class="trigger-btn severity-critical" onclick="triggerAnomaly('cpu_spike', 90, 60)">
                        <div class="title">🔥 CPU Spike</div>
                        <div class="desc">CPU tăng đột ngột lên 95% trong 60 giây</div>
                    </button>
                    <button class="trigger-btn severity-critical" onclick="triggerAnomaly('memory_leak', 85, 120)">
                        <div class="title">💾 Memory Leak</div>
                        <div class="desc">Rò rỉ bộ nhớ nghiêm trọng kéo dài 2 phút</div>
                    </button>
                    <button class="trigger-btn severity-high" onclick="triggerAnomaly('database_slow', 80, 90)">
                        <div class="title">🐌 Database Slow</div>
                        <div class="desc">Truy vấn database chậm bất thường</div>
                    </button>
                    <button class="trigger-btn severity-high" onclick="triggerAnomaly('network_latency', 75, 60)">
                        <div class="title">🌐 Network Latency</div>
                        <div class="desc">Độ trễ mạng tăng cao giữa các services</div>
                    </button>
                    <button class="trigger-btn severity-critical" onclick="triggerAnomaly('auth_failure', 95, 45)">
                        <div class="title">🔒 Auth Failures</div>
                        <div class="desc">Nhiều lần đăng nhập thất bại liên tiếp</div>
                    </button>
                    <button class="trigger-btn severity-high" onclick="triggerAnomaly('payment_fraud', 88, 30)">
                        <div class="title">💳 Payment Fraud</div>
                        <div class="desc">Phát hiện giao dịch thanh toán gian lận</div>
                    </button>
                    <button class="trigger-btn severity-medium" onclick="triggerAnomaly('api_errors', 70, 60)">
                        <div class="title">⚠️ API Errors</div>
                        <div class="desc">Tỷ lệ lỗi API tăng cao bất thường</div>
                    </button>
                    <button class="trigger-btn severity-high" onclick="triggerAnomaly('disk_full', 82, 90)">
                        <div class="title">💿 Disk Full</div>
                        <div class="desc">Dung lượng đĩa gần đầy, cần xử lý ngay</div>
                    </button>
                </div>
                
                <div class="custom-form">
                    <h3>⚙️ Tùy Chỉnh Sự Cố</h3>
                    <div class="custom-form-layout">
                        <div class="form-row">
                            <div class="form-group">
                                <label>
                                    📋 Loại Sự Cố
                                    <span class="hint">(20 kịch bản infrastructure)</span>
                                </label>
                                <select id="customAnomalyType">
                                    <option value="">-- Chọn loại sự cố --</option>
                                    <optgroup label="🔴 CRITICAL">
                                        <option value="memory_leak">💾 Memory Leak - Java Application</option>
                                        <option value="db_pool_exhaustion">🗄️ Database Pool Exhaustion</option>
                                        <option value="container_oom">🐳 Container Out of Memory</option>
                                    </optgroup>
                                    <optgroup label="🟠 HIGH">
                                        <option value="cpu_spike">🔥 CPU Spike - Application Server</option>
                                        <option value="disk_io_bottleneck">💿 Disk I/O Bottleneck</option>
                                        <option value="network_latency">🌐 Network Latency Spike</option>
                                        <option value="api_degradation">⚡ API Response Degradation</option>
                                        <option value="thread_pool_saturation">🧵 Thread Pool Saturation</option>
                                        <option value="load_balancer_uneven">⚖️ Load Balancer Uneven</option>
                                        <option value="database_deadlock">🔒 Database Deadlock</option>
                                        <option value="gc_pressure">♻️ GC Pressure</option>
                                        <option value="dns_resolution_slow">🔍 DNS Resolution Slow</option>
                                        <option value="rate_limit_exceeded">🚫 Rate Limit Exceeded</option>
                                        <option value="replica_lag">📊 Database Replica Lag</option>
                                    </optgroup>
                                    <optgroup label="🟡 MEDIUM">
                                        <option value="cache_invalidation">💨 Cache Invalidation Storm</option>
                                        <option value="message_queue_backlog">📬 Message Queue Backlog</option>
                                        <option value="connection_timeout">⏱️ Connection Timeout</option>
                                        <option value="service_mesh_failure">🕸️ Service Mesh Failure</option>
                                        <option value="ssl_handshake_failure">🔐 SSL Handshake Failure</option>
                                        <option value="circuit_breaker_open">🔌 Circuit Breaker Open</option>
                                    </optgroup>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>📊 Cường Độ</label>
                                <input type="number" id="customIntensity" value="80" min="0" max="100">
                                <span class="helper-text">0-100 điểm</span>
                            </div>
                            <div class="form-group">
                                <label>⏱️ Thời Gian</label>
                                <input type="number" id="customDuration" value="60" min="10" max="600">
                                <span class="helper-text">10-600 giây</span>
                            </div>
                            <div class="form-group">
                                <button class="btn-primary" onclick="triggerCustomAnomaly()">
                                    🚀 Tạo Sự Cố
                                </button>
                            </div>
                        </div>
                        
                        <div class="info-box">
                            💡 <strong>Hướng dẫn:</strong> Cường độ càng cao thì sự cố càng nghiêm trọng. Thời gian là khoảng thời gian sự cố sẽ kéo dài và tự động kết thúc.
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="icon">⚡</span>
                    <h2>Tạo Log Liên Tục</h2>
                </div>
                <p class="card-description">Hệ thống tự động tạo log liên tục với tần suất bất thường thấp phù hợp với thực tế</p>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="normalLogs">0</div>
                        <div class="stat-label">Log Bình Thường</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, var(--secondary) 0%, #7c3aed 100%);">
                        <div class="stat-value" id="anomalyCount">0</div>
                        <div class="stat-label">Sự Cố Đã Tạo</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, var(--success) 0%, #059669 100%);">
                        <div class="stat-value" id="currentRate">0</div>
                        <div class="stat-label">Log/Giây</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, var(--accent) 0%, #db2777 100%);">
                        <div class="stat-value" id="anomalyRate">0.00%</div>
                        <div class="stat-label">Tỷ Lệ Bất Thường</div>
                    </div>
                </div>
                
                <div class="config-row">
                    <label>Tốc độ log bình thường</label>
                    <input type="number" id="normalRate" value="100" min="10" max="1000">
                    <span class="hint">log/giây</span>
                </div>
                <div class="config-row">
                    <label>Tần suất bất thường</label>
                    <input type="number" id="anomalyFreq" value="5000" min="100" max="50000" oninput="updateAnomalyPercent()">
                    <span class="hint" id="anomalyPercent">(0.02%)</span>
                </div>
                <div class="config-row">
                    <label>Thời gian mỗi sự cố</label>
                    <input type="number" id="anomalyDuration" value="30" min="10" max="300">
                    <span class="hint">giây</span>
                </div>
                
                <button class="toggle-btn" id="toggleBtn" onclick="toggleContinuous()">
                    🚀 Bắt Đầu Tạo Log
                </button>
            </div>
        </div>
        
        <script>
            let continuousEnabled = false;
            
            async function triggerAnomaly(type, intensity, duration) {
                const response = await fetch('/api/anomaly/trigger', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        anomaly_type: type,
                        intensity: intensity,
                        duration_seconds: duration
                    })
                });
                
                const result = await response.json();
                alert(`✅ Đã tạo sự cố thủ công: ${type}\\nCường độ: ${intensity}%\\nThời gian: ${duration}s\\nID: ${result.execution_id}`);
                
                // Reload manual incidents after creating a new one
                setTimeout(() => {
                    loadManualIncidents();
                }, 500);
            }
            
            async function loadManualIncidents() {
                const container = document.getElementById('manualIncidentsList');
                container.innerHTML = '<div class="loading-indicator">Đang tải dữ liệu...</div>';
                
                try {
                    const response = await fetch('/api/executions/manual');
                    const incidents = await response.json();
                    
                    if (incidents.length === 0) {
                        container.innerHTML = `
                            <div class="empty-state">
                                <div class="icon">🖐️</div>
                                <p>Chưa có sự cố thủ công nào được tạo</p>
                                <p style="font-size: 0.85rem; margin-top: 0.5rem;">Tạo sự cố thủ công từ các nút ở phần dưới để theo dõi tại đây</p>
                            </div>
                        `;
                        return;
                    }
                    
                    // Sort incidents by timestamp (newest first)
                    incidents.sort((a, b) => new Date(b.started_at || 0) - new Date(a.started_at || 0));
                    
                    container.innerHTML = incidents.map(incident => {
                        const statusClass = incident.status.toLowerCase();
                        const statusIcon = incident.status === 'running' ? '⚡' : 
                                        incident.status === 'completed' ? '✅' : '❌';
                        
                        const startTime = incident.started_at ? new Date(incident.started_at) : null;
                        const endTime = incident.completed_at ? new Date(incident.completed_at) : null;
                        const duration = startTime && endTime ? 
                            Math.round((endTime - startTime) / 1000) : 
                            (startTime ? Math.round((new Date() - startTime) / 1000) : 0);
                        
                        const getAnomalyDisplayName = (type) => {
                            const displayNames = {
                                'cpu_spike': '🔥 CPU Spike',
                                'memory_leak': '💾 Memory Leak', 
                                'database_slow': '🐌 Database Slow',
                                'network_latency': '🌐 Network Latency',
                                'auth_failure': '🔒 Auth Failures', 
                                'payment_fraud': '💳 Payment Fraud',
                                'api_errors': '⚠️ API Errors',
                                'disk_full': '💿 Disk Full'
                            };
                            return displayNames[type] || `📊 ${type}`;
                        };
                        
                        return `
                            <div class="incident-card manual ${statusClass}">
                                <div class="incident-header">
                                    <div class="incident-title">
                                        ${getAnomalyDisplayName(incident.anomaly_type || 'unknown')}
                                        <span class="incident-badge">Thủ công</span>
                                    </div>
                                    <div class="incident-status status-${statusClass}">
                                        ${statusIcon} ${incident.status.charAt(0).toUpperCase() + incident.status.slice(1)}
                                    </div>
                                </div>
                                <div class="incident-details">
                                    <div class="incident-detail">
                                        <span class="label">ID:</span>
                                        <span>${incident.id}</span>
                                    </div>
                                    <div class="incident-detail">
                                        <span class="label">Loại:</span>
                                        <span>${incident.anomaly_type || 'Unknown'}</span>
                                    </div>
                                    <div class="incident-detail">
                                        <span class="label">Log:</span>
                                        <span>${incident.logs_generated || 0} logs</span>
                                    </div>
                                    <div class="incident-detail">
                                        <span class="label">Thời gian:</span>
                                        <span>${duration} giây</span>
                                    </div>
                                    <div class="incident-detail">
                                        <span class="label">Cường độ:</span>
                                        <span>${incident.config?.parameters?.intensity || 'N/A'}%</span>
                                    </div>
                                </div>
                                ${incident.started_at ? `
                                    <div class="incident-timestamp">
                                        🔖 Bắt đầu: ${startTime.toLocaleString('vi-VN')}
                                        ${endTime ? ` | Kết thúc: ${endTime.toLocaleString('vi-VN')}` : ' (đang chạy...)'}
                                    </div>
                                ` : ''}
                                ${incident.error_message ? `
                                    <div class="incident-timestamp" style="color: var(--danger)">
                                        ❌ Lỗi: ${incident.error_message}
                                    </div>
                                ` : ''}
                            </div>
                        `;
                    }).join('');
                    
                } catch (error) {
                    console.error('Failed to load manual incidents:', error);
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="icon">❌</div>
                            <p>Không thể tải dữ liệu sự cố thủ công</p>
                            <button class="btn-refresh" style="margin-top: 1rem;" onclick="loadManualIncidents()">Thử lại</button>
                        </div>
                    `;
                }
            }
            
            async function triggerCustomAnomaly() {
                const type = document.getElementById('customAnomalyType').value;
                const intensity = parseInt(document.getElementById('customIntensity').value);
                const duration = parseInt(document.getElementById('customDuration').value);
                
                if (!type) {
                    alert('⚠️ Vui lòng chọn loại sự cố');
                    return;
                }
                
                await triggerAnomaly(type, intensity, duration);
            }
            
            function updateAnomalyPercent() {
                const freq = parseInt(document.getElementById('anomalyFreq').value);
                const percent = ((1 / freq) * 100).toFixed(4);
                document.getElementById('anomalyPercent').textContent = `(${percent}%)`;
            }
            
            async function toggleContinuous() {
                const btn = document.getElementById('toggleBtn');
                
                if (!continuousEnabled) {
                    const config = {
                        enabled: true,
                        normal_log_rate: parseInt(document.getElementById('normalRate').value),
                        anomaly_frequency: parseInt(document.getElementById('anomalyFreq').value),
                        anomaly_duration: parseInt(document.getElementById('anomalyDuration').value)
                    };
                    
                    const response = await fetch('/api/continuous/start', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(config)
                    });
                    
                    if (response.ok) {
                        continuousEnabled = true;
                        btn.textContent = '⏸️ Dừng Tạo Log';
                        btn.classList.add('active');
                    }
                } else {
                    await fetch('/api/continuous/stop', {method: 'POST'});
                    continuousEnabled = false;
                    btn.textContent = '🚀 Bắt Đầu Tạo Log';
                    btn.classList.remove('active');
                }
            }
            
            async function loadContinuousStats() {
                try {
                    const response = await fetch('/api/continuous/stats');
                    const stats = await response.json();
                    
                    document.getElementById('normalLogs').textContent = stats.normal_logs_generated.toLocaleString();
                    document.getElementById('anomalyCount').textContent = stats.anomalies_injected;
                    document.getElementById('currentRate').textContent = stats.current_rate;
                    document.getElementById('anomalyRate').textContent = stats.anomaly_rate.toFixed(4) + '%';
                    
                    if (stats.enabled && !continuousEnabled) {
                        continuousEnabled = true;
                        const btn = document.getElementById('toggleBtn');
                        btn.textContent = '⏸️ Dừng Tạo Log';
                        btn.classList.add('active');
                    }
                } catch (error) {
                    console.error('Failed to load stats:', error);
                }
            }
            
            loadContinuousStats();
            loadManualIncidents();
            setInterval(loadContinuousStats, 2000);
            setInterval(loadManualIncidents, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/scenarios", response_model=List[Scenario])
async def list_scenarios(
    category: Optional[ScenarioCategory] = None,
    severity: Optional[SeverityLevel] = None
):
    """List all scenarios with optional filters"""
    scenarios = list(scenarios_db.values())
    
    if category:
        scenarios = [s for s in scenarios if s.category == category]
    if severity:
        scenarios = [s for s in scenarios if s.severity == severity]
    
    return scenarios

@app.get("/api/scenarios/{scenario_id}", response_model=Scenario)
async def get_scenario(scenario_id: str):
    """Get specific scenario details"""
    if scenario_id not in scenarios_db:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenarios_db[scenario_id]

@app.post("/api/executions", response_model=Execution)
async def create_execution(config: ScenarioConfig, background_tasks: BackgroundTasks):
    """Start a new scenario execution"""
    if config.scenario_id not in scenarios_db:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    execution_id = str(uuid.uuid4())
    execution = Execution(
        id=execution_id,
        scenario_id=config.scenario_id,
        status=ExecutionStatus.PENDING,
        config=config
    )
    executions_db[execution_id] = execution
    
    # Start execution in background
    background_tasks.add_task(run_execution, execution_id)
    
    return execution

@app.get("/api/executions", response_model=List[Execution])
async def list_executions():
    """List all executions"""
    return list(executions_db.values())

@app.get("/api/executions/manual")
async def list_manual_executions():
    """List all manual anomaly executions"""
    manual_executions = [e for e in executions_db.values() if e.is_manual]
    return manual_executions

@app.get("/api/executions/{execution_id}", response_model=Execution)
async def get_execution(execution_id: str):
    """Get execution status"""
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")
    return executions_db[execution_id]

@app.post("/api/executions/{execution_id}/stop")
async def stop_execution(execution_id: str):
    """Stop a running execution"""
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    execution = executions_db[execution_id]
    if execution.status == ExecutionStatus.RUNNING:
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
    
    return {"message": "Execution stopped"}

async def run_execution(execution_id: str):
    """Background task to run scenario execution"""
    execution = executions_db[execution_id]
    execution.status = ExecutionStatus.RUNNING
    execution.started_at = datetime.now()
    
    try:
        # Notify Pattern Generator
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{PATTERN_GENERATOR_URL}/api/generate",
                    json={
                        "execution_id": execution_id,
                        "scenario_id": execution.config.scenario_id,
                        "parameters": execution.config.parameters,
                        "duration": execution.config.duration_seconds,
                        "rate": execution.config.log_rate
                    },
                    timeout=5.0
                )
            except Exception as e:
                print(f"Pattern Generator not available: {e}")
        
        # Simulate execution
        duration = execution.config.duration_seconds
        rate = execution.config.log_rate
        
        for i in range(duration):
            if execution.status != ExecutionStatus.RUNNING:
                break
            
            execution.logs_generated += rate
            await asyncio.sleep(1)
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        
    except Exception as e:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(e)
        execution.completed_at = datetime.now()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "scenario-orchestrator",
        "scenarios_count": len(scenarios_db),
        "active_executions": len([e for e in executions_db.values() if e.status == ExecutionStatus.RUNNING])
    }

@app.post("/api/continuous/start")
async def start_continuous(config: ContinuousConfig, background_tasks: BackgroundTasks):
    """Start continuous log generation with low-frequency anomalies"""
    global continuous_state
    
    continuous_state["enabled"] = True
    continuous_state["config"] = config
    continuous_state["normal_logs_generated"] = 0
    continuous_state["anomalies_injected"] = 0
    continuous_state["last_anomaly_at"] = None
    continuous_state["current_anomaly"] = None
    
    # Start background task
    background_tasks.add_task(run_continuous_generation)
    
    return {
        "message": "Continuous generation started",
        "config": config.dict()
    }

@app.post("/api/continuous/stop")
async def stop_continuous():
    """Stop continuous log generation"""
    global continuous_state
    continuous_state["enabled"] = False
    
    return {
        "message": "Continuous generation stopped",
        "stats": {
            "normal_logs": continuous_state["normal_logs_generated"],
            "anomalies": continuous_state["anomalies_injected"]
        }
    }

@app.get("/api/continuous/stats")
async def get_continuous_stats():
    """Get continuous generation statistics"""
    total_logs = continuous_state["normal_logs_generated"]
    anomalies = continuous_state["anomalies_injected"]
    anomaly_rate = (anomalies / max(total_logs, 1)) * 100 if total_logs > 0 else 0
    
    return {
        "enabled": continuous_state["enabled"],
        "normal_logs_generated": total_logs,
        "anomalies_injected": anomalies,
        "anomaly_rate": anomaly_rate,
        "current_rate": continuous_state["config"].normal_log_rate if continuous_state["enabled"] else 0,
        "current_anomaly": continuous_state["current_anomaly"]
    }

async def run_continuous_generation():
    """Background task for continuous log generation"""
    global continuous_state
    
    print("[v0] Starting continuous generation with realistic log distribution...")
    print(f"[v0] Configured for {len(LOG_TYPE_FREQUENCIES)} different log types")
    
    while continuous_state["enabled"]:
        config = continuous_state["config"]
        
        # Check if we should inject an anomaly
        should_inject_anomaly = (
            continuous_state["normal_logs_generated"] > 0 and
            continuous_state["normal_logs_generated"] % config.anomaly_frequency == 0 and
            continuous_state["current_anomaly"] is None
        )
        
        if should_inject_anomaly:
            # Select random scenario for anomaly
            scenario_id = random.choice(list(scenarios_db.keys()))
            continuous_state["current_anomaly"] = {
                "scenario_id": scenario_id,
                "started_at": datetime.now(),
                "duration": config.anomaly_duration
            }
            continuous_state["anomalies_injected"] += 1
            continuous_state["last_anomaly_at"] = datetime.now()
            
            print(f"[v0] Injecting anomaly #{continuous_state['anomalies_injected']}: {scenario_id}")
        
        # Generate logs with realistic distribution
        try:
            async with httpx.AsyncClient() as client:
                # Determine if currently in anomaly period
                is_anomaly = False
                anomaly_score = 0.0
                
                if continuous_state["current_anomaly"]:
                    anomaly = continuous_state["current_anomaly"]
                    elapsed = (datetime.now() - anomaly["started_at"]).total_seconds()
                    
                    if elapsed < anomaly["duration"]:
                        is_anomaly = True
                        # Anomaly score varies during the anomaly period (bell curve)
                        progress = elapsed / anomaly["duration"]
                        # Peak at middle of anomaly period
                        anomaly_score = 60 + 35 * math.sin(progress * math.pi)
                    else:
                        # Anomaly period ended
                        print(f"[v0] Anomaly ended: {anomaly['scenario_id']}")
                        continuous_state["current_anomaly"] = None
                
                log_type = select_realistic_log_type()
                
                try:
                    await client.post(
                        f"{LOG_SYNTHESIS_URL}/api/synthesize",
                        json={
                            "log_type": log_type,
                            "scenario_id": continuous_state["current_anomaly"]["scenario_id"] if is_anomaly else "NORMAL",
                            "count": config.normal_log_rate,
                            "anomaly_score": anomaly_score
                        },
                        timeout=5.0
                    )
                    
                    continuous_state["normal_logs_generated"] += config.normal_log_rate
                    
                    if continuous_state["normal_logs_generated"] % 10000 == 0:
                        print(f"[v0] Generated {continuous_state['normal_logs_generated']:,} logs, "
                              f"{continuous_state['anomalies_injected']} anomalies injected")
                    
                except Exception as e:
                    print(f"[v0] Log synthesis error: {e}")
        
        except Exception as e:
            print(f"[v0] Continuous generation error: {e}")
        
        # Wait 1 second before next batch
        await asyncio.sleep(1)
    
    print("[v0] Continuous generation stopped")

# New endpoints for infrastructure scenarios
@app.get("/api/infrastructure-scenarios")
async def list_infrastructure_scenarios(severity: Optional[str] = None):
    """List all 20 infrastructure anomaly scenarios"""
    if severity:
        scenarios = get_scenarios_by_severity(severity)
    else:
        scenarios = get_all_infrastructure_scenarios()
    return scenarios

@app.get("/api/infrastructure-scenarios/{scenario_id}")
async def get_infrastructure_scenario(scenario_id: str):
    """Get detailed infrastructure scenario configuration"""
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Infrastructure scenario not found")
    return scenario

@app.post("/api/infrastructure-scenarios/{scenario_id}/simulate")
async def simulate_infrastructure_scenario(
    scenario_id: str,
    duration_seconds: int = 300,
    intensity: float = 1.0,
    background_tasks: BackgroundTasks = None
):
    """Simulate a specific infrastructure scenario with customizable parameters"""
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Infrastructure scenario not found")
    
    execution_id = str(uuid.uuid4())
    execution = Execution(
        id=execution_id,
        scenario_id=scenario_id,
        status=ExecutionStatus.PENDING,
        config=ScenarioConfig(
            scenario_id=scenario_id,
            parameters={"intensity": intensity, "scenario_config": scenario},
            duration_seconds=duration_seconds,
            log_rate=100
        )
    )
    executions_db[execution_id] = execution
    
    # Start simulation in background
    background_tasks.add_task(run_infrastructure_simulation, execution_id, scenario, intensity)
    
    return {
        "execution_id": execution_id,
        "scenario": scenario["name"],
        "duration": duration_seconds,
        "intensity": intensity,
        "status": "started"
    }

async def run_infrastructure_simulation(execution_id: str, scenario: Dict[str, Any], intensity: float):
    """Run infrastructure scenario simulation with realistic metrics"""
    execution = executions_db[execution_id]
    execution.status = ExecutionStatus.RUNNING
    execution.started_at = datetime.now()
    
    try:
        duration = execution.config.duration_seconds
        log_patterns = scenario.get("log_patterns", ["application_log"])
        
        # Calculate anomaly score based on intensity and scenario metrics
        base_anomaly_score = 60 + (intensity * 35)  # 60-95 range
        
        async with httpx.AsyncClient() as client:
            for i in range(duration):
                if execution.status != ExecutionStatus.RUNNING:
                    break
                
                # Vary anomaly score over time (bell curve pattern)
                progress = i / duration
                current_anomaly_score = base_anomaly_score * math.sin(progress * math.pi)
                
                # Generate logs for each pattern type
                for log_pattern in log_patterns:
                    try:
                        await client.post(
                            f"{LOG_SYNTHESIS_URL}/api/synthesize",
                            json={
                                "log_type": log_pattern,
                                "scenario_id": scenario["id"],
                                "count": 10,
                                "anomaly_score": current_anomaly_score,
                                "scenario_metadata": {
                                    "name": scenario["name"],
                                    "severity": scenario["severity"],
                                    "metrics": scenario["metrics"],
                                    "root_causes": scenario["root_causes"]
                                }
                            },
                            timeout=5.0
                        )
                        execution.logs_generated += 10
                    except Exception as e:
                        print(f"[v0] Log synthesis error: {e}")
                
                await asyncio.sleep(1)
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        print(f"[v0] Infrastructure simulation completed: {scenario['name']}")
        
    except Exception as e:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(e)
        execution.completed_at = datetime.now()
        print(f"[v0] Infrastructure simulation failed: {e}")

@app.post("/api/anomaly/trigger")
async def trigger_manual_anomaly(
    anomaly_type: str,
    intensity: float,
    duration_seconds: int,
    background_tasks: BackgroundTasks
):
    """Manually trigger a specific anomaly"""
    execution_id = str(uuid.uuid4())[:8]
    
    execution = Execution(
        id=execution_id,
        scenario_id=f"MANUAL_{anomaly_type.upper()}",
        status=ExecutionStatus.PENDING,
        config=ScenarioConfig(
            scenario_id=f"MANUAL_{anomaly_type.upper()}",
            parameters={"intensity": intensity, "anomaly_type": anomaly_type},
            duration_seconds=duration_seconds,
            log_rate=100
        ),
        is_manual=True,
        anomaly_type=anomaly_type
    )
    executions_db[execution_id] = execution
    
    # Start manual anomaly generation
    background_tasks.add_task(run_manual_anomaly, execution_id, anomaly_type, intensity, duration_seconds)
    
    return {
        "execution_id": execution_id,
        "anomaly_type": anomaly_type,
        "intensity": intensity,
        "duration": duration_seconds,
        "is_manual": True,
        "status": "started"
    }

async def run_manual_anomaly(execution_id: str, anomaly_type: str, intensity: float, duration: int):
    """Run manual anomaly generation"""
    execution = executions_db[execution_id]
    execution.status = ExecutionStatus.RUNNING
    execution.started_at = datetime.now()
    
    print(f"[v0] Manual anomaly triggered: {anomaly_type} (intensity: {intensity}%, duration: {duration}s)")
    
    try:
        async with httpx.AsyncClient() as client:
            for i in range(duration):
                if execution.status != ExecutionStatus.RUNNING:
                    break
                
                # Calculate anomaly score with bell curve
                progress = i / duration
                anomaly_score = intensity * math.sin(progress * math.pi)
                
                # Select appropriate log types based on anomaly type
                log_types = get_log_types_for_anomaly(anomaly_type)
                
                for log_type in log_types:
                    try:
                        await client.post(
                            f"{LOG_SYNTHESIS_URL}/api/synthesize",
                            json={
                                "log_type": log_type,
                                "scenario_id": f"MANUAL_{anomaly_type.upper()}",
                                "count": 20,
                                "anomaly_score": anomaly_score
                            },
                            timeout=5.0
                        )
                        execution.logs_generated += 20
                    except Exception as e:
                        print(f"[v0] Log synthesis error: {e}")
                
                await asyncio.sleep(1)
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        print(f"[v0] Manual anomaly completed: {anomaly_type}")
        
    except Exception as e:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(e)
        execution.completed_at = datetime.now()
        print(f"[v0] Manual anomaly failed: {e}")

def get_log_types_for_anomaly(anomaly_type: str) -> List[str]:
    """Get appropriate log types for specific anomaly"""
    anomaly_log_mapping = {
        "cpu_spike": ["server_log", "container_log", "application_log"],
        "memory_leak": ["server_log", "application_log", "container_log"],
        "database_slow": ["database_query_log", "database_transaction_log", "application_log"],
        "network_latency": ["network_log", "api_gateway_log", "load_balancer_log"],
        "auth_failure": ["authentication_log", "security_log", "waf_log"],
        "payment_fraud": ["payment_transaction_log", "fraud_detection_log", "risk_assessment_log"],
        "api_errors": ["api_gateway_log", "application_log", "microservice_log"],
        "disk_full": ["storage_log", "server_log", "database_backup_log"]
    }
    
    return anomaly_log_mapping.get(anomaly_type, ["application_log", "server_log"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
