"""
Specialized Logs - 2 loại log
Logs chuyên biệt cho các mục đích đặc thù
"""

import random
from datetime import datetime
from .common import *

class SpecializedLogs:
    """Generator cho Specialized Logs"""
    
    @staticmethod
    def generate_blockchain_log(anomaly_score: float = 0.0) -> dict:
        """
        Blockchain/DLT Logs
        Log cho các giao dịch blockchain và distributed ledger
        """
        operations = ["TRANSACTION", "SMART_CONTRACT", "CONSENSUS", "BLOCK_CREATION", "VALIDATION"]
        networks = ["Ethereum", "Hyperledger Fabric", "Corda", "Private Chain"]
        
        is_anomaly = anomaly_score > 0.7
        
        operation = random.choice(operations)
        network = random.choice(networks)
        
        if is_anomaly:
            status = "FAILED"
            error = random.choice([
                "Consensus timeout",
                "Invalid signature",
                "Insufficient gas",
                "Smart contract execution failed",
                "Network partition detected"
            ])
            confirmations = 0
        else:
            status = "SUCCESS"
            error = None
            confirmations = random.randint(6, 50)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "blockchain",
            "network": network,
            "operation": operation,
            "transaction_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
            "block_number": random.randint(1000000, 9999999),
            "from_address": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
            "to_address": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
            "value": round(random.uniform(0.001, 100.0), 6),
            "gas_used": random.randint(21000, 500000),
            "gas_price_gwei": round(random.uniform(1, 100), 2),
            "status": status,
            "confirmations": confirmations,
            "error": error,
            "smart_contract": f"0x{''.join(random.choices('0123456789abcdef', k=40))}" if operation == "SMART_CONTRACT" else None,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_iot_device_log(anomaly_score: float = 0.0) -> dict:
        """
        IoT Device Logs
        Log từ các thiết bị IoT (ATM, POS, sensors)
        """
        device_types = ["ATM", "POS_TERMINAL", "CARD_READER", "BIOMETRIC_SCANNER", "SECURITY_CAMERA"]
        events = ["TRANSACTION", "MAINTENANCE", "ERROR", "ALERT", "STATUS_UPDATE"]
        
        is_anomaly = anomaly_score > 0.7
        
        device_type = random.choice(device_types)
        event = random.choice(events)
        
        if is_anomaly:
            status = "CRITICAL"
            event = random.choice(["ERROR", "ALERT"])
            message = random.choice([
                "Cash dispenser jam detected",
                "Card reader malfunction",
                "Tampering attempt detected",
                "Network connectivity lost",
                "Low cash warning",
                "Unauthorized access attempt"
            ])
            battery_level = random.randint(0, 20) if device_type != "ATM" else None
        else:
            status = "NORMAL"
            message = "Device operating normally"
            battery_level = random.randint(50, 100) if device_type != "ATM" else None
        
        location = random.choice(VIETNAMESE_CITIES)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "iot_device",
            "device_type": device_type,
            "device_id": f"{device_type}-{random.randint(1000, 9999)}",
            "event": event,
            "status": status,
            "message": message,
            "location": {
                "city": location,
                "address": f"{random.randint(1, 999)} Đường {random.choice(['Lê Lợi', 'Trần Hưng Đạo', 'Nguyễn Huệ', 'Hai Bà Trưng'])}",
                "coordinates": {
                    "lat": round(random.uniform(8.0, 23.0), 6),
                    "lon": round(random.uniform(102.0, 109.0), 6)
                }
            },
            "firmware_version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
            "uptime_hours": random.randint(0, 8760),
            "battery_level": battery_level,
            "temperature_celsius": round(random.uniform(15, 45), 1),
            "last_maintenance": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            "anomaly_score": anomaly_score
        }
