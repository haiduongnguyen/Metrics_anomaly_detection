"""
User Behavior & Analytics Logs
Danh mục VII: 6 loại log về hành vi người dùng và phân tích
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from .common import *


class AnalyticsLogs:
    """Generator cho các loại log phân tích hành vi người dùng"""
    
    @staticmethod
    def generate_user_activity_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """VII.1 - User Activity Logs: Log hoạt động người dùng"""
        
        activities = [
            "login", "logout", "view_balance", "view_statement",
            "update_profile", "change_password", "add_beneficiary",
            "view_offers", "apply_loan", "open_account"
        ]
        
        session_duration = random.randint(60, 3600)
        
        if anomaly_score > 0.7:
            activity_pattern = "unusual"
            flags = random.sample(["off_hours", "rapid_clicks", "bot_like", "location_jump"], k=random.randint(1, 2))
        else:
            activity_pattern = "normal"
            flags = []
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "user_activity",
            "category": "analytics",
            "user_id": f"USR{random.randint(100000, 999999)}",
            "session_id": f"SES{random.randint(100000, 999999)}",
            "activity": random.choice(activities),
            "activity_pattern": activity_pattern,
            "flags": flags,
            "page_url": f"/banking/{random.choice(['dashboard', 'transfer', 'accounts', 'cards'])}",
            "referrer": random.choice(["direct", "google", "facebook", "email"]),
            "device": random.choice(["mobile", "desktop", "tablet"]),
            "os": random.choice(["iOS", "Android", "Windows", "MacOS"]),
            "browser": random.choice(["Chrome", "Safari", "Firefox", "Edge"]),
            "ip_address": random_ip(),
            "location": random.choice(VIETNAMESE_CITIES),
            "session_duration_seconds": session_duration,
            "pages_viewed": random.randint(1, 20),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_clickstream_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """VII.2 - Clickstream Logs: Log luồng click"""
        
        elements = [
            "transfer_button", "balance_link", "menu_icon",
            "logout_button", "help_icon", "notification_bell"
        ]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "clickstream",
            "category": "analytics",
            "user_id": f"USR{random.randint(100000, 999999)}",
            "session_id": f"SES{random.randint(100000, 999999)}",
            "element_id": random.choice(elements),
            "element_type": random.choice(["button", "link", "icon", "input"]),
            "page_url": f"/banking/{random.choice(['dashboard', 'transfer', 'accounts'])}",
            "x_coordinate": random.randint(0, 1920),
            "y_coordinate": random.randint(0, 1080),
            "viewport_width": random.choice([375, 768, 1024, 1920]),
            "viewport_height": random.choice([667, 1024, 768, 1080]),
            "time_on_page_seconds": random.randint(1, 300),
            "scroll_depth_percent": random.randint(0, 100),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_feature_usage_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """VII.3 - Feature Usage Logs: Log sử dụng tính năng"""
        
        features = [
            "fund_transfer", "bill_payment", "card_management",
            "loan_application", "investment", "savings_account"
        ]
        
        feature = random.choice(features)
        usage_count = random.randint(1, 50)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "feature_usage",
            "category": "analytics",
            "user_id": f"USR{random.randint(100000, 999999)}",
            "feature_name": feature,
            "feature_category": random.choice(["transaction", "account", "service"]),
            "usage_count": usage_count,
            "success_count": usage_count - random.randint(0, 3),
            "failure_count": random.randint(0, 3),
            "avg_completion_time_seconds": random.randint(30, 300),
            "user_segment": random.choice(["premium", "regular", "new"]),
            "device_type": random.choice(["mobile", "web"]),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_conversion_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """VII.4 - Conversion Tracking Logs: Log theo dõi chuyển đổi"""
        
        funnels = [
            "account_opening", "loan_application", "card_application",
            "investment_signup", "insurance_purchase"
        ]
        
        funnel = random.choice(funnels)
        steps = ["landing", "form_start", "form_complete", "verification", "approval"]
        current_step = random.choice(steps)
        
        converted = anomaly_score < 0.5
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "conversion_tracking",
            "category": "analytics",
            "user_id": f"USR{random.randint(100000, 999999)}",
            "funnel_name": funnel,
            "current_step": current_step,
            "steps_completed": steps.index(current_step) + 1,
            "total_steps": len(steps),
            "converted": converted,
            "time_to_convert_minutes": random.randint(5, 120) if converted else None,
            "drop_off_point": None if converted else current_step,
            "campaign_source": random.choice(["organic", "paid_search", "social", "email"]),
            "device_type": random.choice(["mobile", "desktop"]),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_ab_test_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """VII.5 - A/B Testing Logs: Log thử nghiệm A/B"""
        
        experiments = [
            "new_dashboard_layout", "simplified_transfer_flow",
            "enhanced_security", "personalized_offers"
        ]
        
        variant = random.choice(["control", "variant_a", "variant_b"])
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "ab_testing",
            "category": "analytics",
            "user_id": f"USR{random.randint(100000, 999999)}",
            "experiment_id": f"EXP{random.randint(1000, 9999)}",
            "experiment_name": random.choice(experiments),
            "variant": variant,
            "converted": random.choice([True, False]),
            "engagement_score": round(random.uniform(0, 100), 2),
            "time_spent_seconds": random.randint(30, 600),
            "interactions_count": random.randint(1, 20),
            "device_type": random.choice(["mobile", "desktop"]),
            "user_segment": random.choice(["new", "active", "dormant"]),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_customer_journey_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """VII.6 - Customer Journey Logs: Log hành trình khách hàng"""
        
        touchpoints = [
            "website_visit", "mobile_app", "call_center",
            "branch_visit", "email", "sms", "push_notification"
        ]
        
        journey_stage = random.choice(["awareness", "consideration", "purchase", "retention", "advocacy"])
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "customer_journey",
            "category": "analytics",
            "customer_id": f"CUS{random.randint(100000, 999999)}",
            "journey_id": f"JRN{random.randint(100000, 999999)}",
            "journey_stage": journey_stage,
            "touchpoint": random.choice(touchpoints),
            "touchpoint_sequence": random.randint(1, 10),
            "channel": random.choice(["digital", "physical", "phone"]),
            "interaction_type": random.choice(["inquiry", "transaction", "complaint", "feedback"]),
            "satisfaction_score": random.randint(1, 5),
            "resolution_status": random.choice(["resolved", "pending", "escalated"]),
            "time_since_last_interaction_hours": random.randint(1, 720),
            "total_interactions": random.randint(1, 50),
            "customer_lifetime_value": round(random.uniform(1000000, 100000000), 2),
            "anomaly_score": anomaly_score
        }


def get_all_analytics_log_types():
    """Trả về danh sách tất cả các loại log phân tích"""
    return [
        "user_activity",
        "clickstream",
        "feature_usage",
        "conversion_tracking",
        "ab_testing",
        "customer_journey"
    ]
