"""
Business Transaction Logs
Danh mục V: 5 loại log về giao dịch nghiệp vụ
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from .common import *


class TransactionLogs:
    """Generator cho các loại log giao dịch nghiệp vụ"""
    
    @staticmethod
    def generate_payment_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """V.1 - Payment Transaction Logs: Log giao dịch thanh toán"""
        
        transaction_id = f"TXN{random.randint(1000000, 9999999)}"
        amount = round(random.uniform(10000, 50000000), 2)
        
        payment_methods = ["card", "bank_transfer", "e_wallet", "qr_code", "cash"]
        
        if anomaly_score > 0.7:
            status = random.choice(["failed", "declined", "suspicious", "flagged"])
            error_code = random.choice(["INSUFFICIENT_FUNDS", "CARD_DECLINED", "FRAUD_DETECTED", "LIMIT_EXCEEDED"])
        else:
            status = "success"
            error_code = None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "payment_transaction",
            "category": "transaction",
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": "VND",
            "payment_method": random.choice(payment_methods),
            "status": status,
            "error_code": error_code,
            "merchant_id": f"MER{random.randint(10000, 99999)}",
            "merchant_name": random.choice(["Vinmart", "Shopee", "Lazada", "Grab", "Tiki"]),
            "customer_id": f"CUS{random.randint(100000, 999999)}",
            "card_last4": f"****{random.randint(1000, 9999)}" if random.choice(payment_methods) == "card" else None,
            "processing_time_ms": random.randint(100, 5000),
            "gateway": random.choice(["VNPay", "MoMo", "ZaloPay", "OnePay"]),
            "ip_address": random_ip(),
            "location": random.choice(VIETNAMESE_CITIES),
            "anomaly_score": anomaly_score,
            "risk_level": "high" if anomaly_score > 0.7 else "low"
        }
    
    @staticmethod
    def generate_transfer_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """V.2 - Fund Transfer Logs: Log chuyển tiền"""
        
        transfer_id = f"TRF{random.randint(1000000, 9999999)}"
        amount = round(random.uniform(100000, 100000000), 2)
        
        if anomaly_score > 0.7:
            status = random.choice(["pending_review", "blocked", "failed"])
            reason = random.choice([
                "Suspicious pattern",
                "Amount limit exceeded",
                "Beneficiary verification failed",
                "AML check triggered"
            ])
        else:
            status = "completed"
            reason = None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "fund_transfer",
            "category": "transaction",
            "transfer_id": transfer_id,
            "amount": amount,
            "currency": "VND",
            "from_account": f"{random.randint(1000000000, 9999999999)}",
            "to_account": f"{random.randint(1000000000, 9999999999)}",
            "from_bank": random.choice(VIETNAMESE_BANKS),
            "to_bank": random.choice(VIETNAMESE_BANKS),
            "transfer_type": random.choice(["internal", "interbank", "international"]),
            "status": status,
            "reason": reason,
            "beneficiary_name": random.choice(VIETNAMESE_NAMES),
            "description": random.choice([
                "Chuyển tiền",
                "Thanh toán hóa đơn",
                "Trả nợ",
                "Hỗ trợ gia đình"
            ]),
            "fee": round(amount * 0.001, 2),
            "processing_time_ms": random.randint(500, 10000),
            "initiated_by": f"USR{random.randint(100000, 999999)}",
            "ip_address": random_ip(),
            "anomaly_score": anomaly_score,
            "risk_level": "high" if anomaly_score > 0.7 else "low"
        }
    
    @staticmethod
    def generate_withdrawal_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """V.3 - ATM/Withdrawal Logs: Log rút tiền ATM"""
        
        withdrawal_id = f"WTH{random.randint(1000000, 9999999)}"
        amount = random.choice([100000, 200000, 500000, 1000000, 2000000, 5000000])
        
        if anomaly_score > 0.7:
            status = random.choice(["declined", "card_retained", "suspicious"])
            error = random.choice([
                "Insufficient balance",
                "Daily limit exceeded",
                "Card blocked",
                "Suspicious activity"
            ])
        else:
            status = "success"
            error = None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "atm_withdrawal",
            "category": "transaction",
            "withdrawal_id": withdrawal_id,
            "amount": amount,
            "currency": "VND",
            "account_number": f"{random.randint(1000000000, 9999999999)}",
            "card_number": f"****{random.randint(1000, 9999)}",
            "atm_id": f"ATM{random.randint(1000, 9999)}",
            "atm_location": random.choice(VIETNAMESE_CITIES),
            "bank": random.choice(VIETNAMESE_BANKS),
            "status": status,
            "error": error,
            "balance_after": round(random.uniform(1000000, 50000000), 2) if status == "success" else None,
            "fee": 3300 if status == "success" else 0,
            "transaction_count_today": random.randint(1, 10),
            "amount_withdrawn_today": amount * random.randint(1, 5),
            "anomaly_score": anomaly_score,
            "risk_level": "high" if anomaly_score > 0.7 else "low"
        }
    
    @staticmethod
    def generate_loan_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """V.4 - Loan Transaction Logs: Log giao dịch vay/trả nợ"""
        
        loan_id = f"LOAN{random.randint(100000, 999999)}"
        principal = round(random.uniform(10000000, 500000000), 2)
        
        transaction_types = ["disbursement", "repayment", "interest_payment", "early_settlement"]
        
        if anomaly_score > 0.7:
            status = random.choice(["overdue", "defaulted", "suspicious"])
            days_overdue = random.randint(1, 90)
        else:
            status = "completed"
            days_overdue = 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "loan_transaction",
            "category": "transaction",
            "loan_id": loan_id,
            "transaction_type": random.choice(transaction_types),
            "customer_id": f"CUS{random.randint(100000, 999999)}",
            "principal_amount": principal,
            "interest_rate": round(random.uniform(6.0, 18.0), 2),
            "payment_amount": round(principal * random.uniform(0.05, 0.2), 2),
            "outstanding_balance": round(principal * random.uniform(0.3, 0.9), 2),
            "status": status,
            "days_overdue": days_overdue,
            "loan_type": random.choice(["personal", "mortgage", "auto", "business"]),
            "term_months": random.choice([12, 24, 36, 60, 120]),
            "payment_method": random.choice(["auto_debit", "bank_transfer", "cash", "check"]),
            "branch": random.choice(VIETNAMESE_CITIES),
            "anomaly_score": anomaly_score,
            "risk_level": "high" if anomaly_score > 0.7 else "low"
        }
    
    @staticmethod
    def generate_forex_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """V.5 - Foreign Exchange Logs: Log giao dịch ngoại hối"""
        
        forex_id = f"FX{random.randint(1000000, 9999999)}"
        
        currencies = ["USD", "EUR", "JPY", "GBP", "AUD", "CNY", "SGD"]
        from_currency = random.choice(currencies)
        to_currency = "VND" if from_currency != "VND" else random.choice(currencies)
        
        amount = round(random.uniform(1000, 100000), 2)
        exchange_rate = round(random.uniform(20000, 30000), 2) if to_currency == "VND" else round(random.uniform(0.00003, 0.00005), 5)
        
        if anomaly_score > 0.7:
            status = random.choice(["pending_compliance", "flagged", "rejected"])
            reason = random.choice([
                "Large transaction review",
                "Source of funds verification",
                "AML check required"
            ])
        else:
            status = "completed"
            reason = None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "forex_transaction",
            "category": "transaction",
            "forex_id": forex_id,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "from_amount": amount,
            "to_amount": round(amount * exchange_rate, 2),
            "exchange_rate": exchange_rate,
            "status": status,
            "reason": reason,
            "customer_id": f"CUS{random.randint(100000, 999999)}",
            "transaction_type": random.choice(["buy", "sell", "swap"]),
            "purpose": random.choice(["travel", "investment", "trade", "remittance"]),
            "fee": round(amount * 0.002, 2),
            "dealer_id": f"DLR{random.randint(100, 999)}",
            "branch": random.choice(VIETNAMESE_CITIES),
            "anomaly_score": anomaly_score,
            "risk_level": "high" if anomaly_score > 0.7 else "low"
        }


def get_all_transaction_log_types():
    """Trả về danh sách tất cả các loại log giao dịch"""
    return [
        "payment_transaction",
        "fund_transfer",
        "atm_withdrawal",
        "loan_transaction",
        "forex_transaction"
    ]
