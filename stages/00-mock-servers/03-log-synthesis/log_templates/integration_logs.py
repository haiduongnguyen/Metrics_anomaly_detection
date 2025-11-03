"""
External Integration Logs - 3 loại log
Logs liên quan đến tích hợp với hệ thống bên ngoài
"""

import random
from datetime import datetime
from .common import *

class IntegrationLogs:
    """Generator cho External Integration Logs"""
    
    @staticmethod
    def generate_api_gateway_log(anomaly_score: float = 0.0) -> dict:
        """
        API Gateway Logs
        Log của API gateway kết nối với các hệ thống bên ngoài
        """
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        endpoints = [
            "/api/v1/payment/process",
            "/api/v1/account/balance",
            "/api/v1/transfer/domestic",
            "/api/v1/customer/verify",
            "/api/v1/card/transaction"
        ]
        partners = ["NAPAS", "VISA", "Mastercard", "VietQR", "PayPal", "Momo", "ZaloPay"]
        
        is_anomaly = anomaly_score > 0.7
        
        method = random.choice(methods)
        endpoint = random.choice(endpoints)
        partner = random.choice(partners)
        
        if is_anomaly:
            status_code = random.choice([401, 403, 429, 500, 502, 503, 504])
            response_time_ms = random.randint(5000, 30000)
            error_message = random.choice([
                "Authentication failed",
                "Rate limit exceeded",
                "Service unavailable",
                "Gateway timeout",
                "Invalid API key"
            ])
        else:
            status_code = random.choice([200, 201, 204])
            response_time_ms = random.randint(50, 500)
            error_message = None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "api_gateway",
            "method": method,
            "endpoint": endpoint,
            "partner": partner,
            "request_id": f"REQ-{random.randint(100000000, 999999999)}",
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size_bytes": random.randint(100, 10000),
            "response_size_bytes": random.randint(200, 50000),
            "client_ip": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "user_agent": random.choice(["Mobile-App/2.1", "Web-Portal/1.5", "Partner-API/3.0"]),
            "error_message": error_message,
            "retry_count": random.randint(1, 5) if status_code >= 500 else 0,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_message_queue_log(anomaly_score: float = 0.0) -> dict:
        """
        Message Queue Logs (Kafka, RabbitMQ)
        Log của hệ thống message queue
        """
        topics = [
            "transaction.created",
            "payment.processed",
            "notification.sent",
            "account.updated",
            "fraud.detected"
        ]
        operations = ["PRODUCE", "CONSUME", "ACK", "NACK", "REQUEUE"]
        
        is_anomaly = anomaly_score > 0.7
        
        topic = random.choice(topics)
        operation = random.choice(operations)
        
        if is_anomaly:
            status = "FAILED"
            operation = random.choice(["NACK", "REQUEUE"])
            error = random.choice([
                "Message processing timeout",
                "Consumer group rebalancing",
                "Deserialization error",
                "Dead letter queue threshold exceeded"
            ])
            lag_messages = random.randint(10000, 100000)
        else:
            status = "SUCCESS"
            error = None
            lag_messages = random.randint(0, 100)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "message_queue",
            "queue_type": random.choice(["Kafka", "RabbitMQ"]),
            "topic": topic,
            "partition": random.randint(0, 9),
            "offset": random.randint(1000000, 9999999),
            "operation": operation,
            "status": status,
            "message_id": f"MSG-{random.randint(100000000, 999999999)}",
            "consumer_group": f"consumer-group-{random.randint(1, 5)}",
            "processing_time_ms": random.randint(10, 5000),
            "message_size_bytes": random.randint(100, 50000),
            "lag_messages": lag_messages,
            "error": error,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_third_party_service_log(anomaly_score: float = 0.0) -> dict:
        """
        Third-party Service Integration Logs
        Log tích hợp với dịch vụ bên thứ ba
        """
        services = [
            "SMS_Gateway",
            "Email_Service",
            "KYC_Verification",
            "Credit_Scoring",
            "Fraud_Detection",
            "Currency_Exchange",
            "Payment_Gateway"
        ]
        providers = ["Twilio", "SendGrid", "eKYC.vn", "FPT.AI", "Viettel", "VNPT", "Stripe"]
        
        is_anomaly = anomaly_score > 0.7
        
        service = random.choice(services)
        provider = random.choice(providers)
        
        if is_anomaly:
            status = "FAILED"
            response_code = random.choice(["TIMEOUT", "AUTH_FAILED", "QUOTA_EXCEEDED", "SERVICE_DOWN"])
            cost_usd = 0
            retry_attempts = random.randint(3, 10)
        else:
            status = "SUCCESS"
            response_code = "OK"
            cost_usd = round(random.uniform(0.001, 0.5), 4)
            retry_attempts = 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "third_party_service",
            "service_name": service,
            "provider": provider,
            "request_id": f"3RD-{random.randint(100000000, 999999999)}",
            "status": status,
            "response_code": response_code,
            "response_time_ms": random.randint(100, 10000),
            "cost_usd": cost_usd,
            "retry_attempts": retry_attempts,
            "data_sent_kb": round(random.uniform(0.1, 100.0), 2),
            "data_received_kb": round(random.uniform(0.1, 100.0), 2),
            "endpoint": f"https://api.{provider.lower()}.com/v1/{service.lower()}",
            "anomaly_score": anomaly_score
        }
