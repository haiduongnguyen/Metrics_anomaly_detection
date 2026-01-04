rules = [
    {
    "name": "High CPU Usage Detection",
    "description": "Detects if CPU usage exceeds a defined threshold for a sustained period.",
    "conditions": {
        "cpu_usage_threshold": 85,
        "duration_minutes": 10
    },
    "actions": {
        "alert": True,
        "log_event": True
    }
    }
    ,
    {
    "name": "Unauthorized Access Attempt",
    "description": "Detects unauthorized access attempts.",
    "conditions": {
        "failed_attempts_threshold": 5,
        "time_window_minutes": 10
    },
    "actions": {
        "alert": True,
        "log_event": True
    }
    }
]