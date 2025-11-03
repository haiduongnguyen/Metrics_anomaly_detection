"""
Pattern Generator Service
Generates realistic patterns and data for anomaly simulation
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import random
import math
import json

app = FastAPI(title="Pattern Generator Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class GenerationRequest(BaseModel):
    execution_id: str
    scenario_id: str
    parameters: Dict[str, Any]
    duration: int
    rate: int

class PatternData(BaseModel):
    pattern_type: str
    data_points: List[Dict[str, Any]]
    metadata: Dict[str, Any]

# Pattern generation functions
class PatternLibrary:
    """Library of pattern generation functions"""
    
    @staticmethod
    def gaussian_spike(duration: int, rate: int, spike_percentage: float = 85) -> List[float]:
        """Generate Gaussian distribution spike pattern"""
        values = []
        for i in range(duration):
            # Create bell curve centered at middle
            x = (i - duration/2) / (duration/6)
            value = spike_percentage * math.exp(-x**2/2)
            values.append(max(0, value + random.gauss(0, 5)))
        return values
    
    @staticmethod
    def step_function(duration: int, rate: int, step_value: float = 90) -> List[float]:
        """Generate step function pattern"""
        values = []
        step_point = duration // 3
        for i in range(duration):
            if i < step_point:
                values.append(random.gauss(20, 5))
            else:
                values.append(random.gauss(step_value, 10))
        return values
    
    @staticmethod
    def sawtooth_pattern(duration: int, rate: int, amplitude: float = 80) -> List[float]:
        """Generate sawtooth pattern for periodic issues"""
        values = []
        period = duration // 4
        for i in range(duration):
            value = (i % period) / period * amplitude
            values.append(value + random.gauss(0, 3))
        return values
    
    @staticmethod
    def exponential_decay(duration: int, rate: int, initial: float = 100) -> List[float]:
        """Generate exponential decay pattern"""
        values = []
        decay_rate = 0.05
        for i in range(duration):
            value = initial * math.exp(-decay_rate * i)
            values.append(max(10, value + random.gauss(0, 5)))
        return values
    
    @staticmethod
    def poisson_events(duration: int, rate: int, lambda_param: float = 5) -> List[int]:
        """Generate Poisson distributed events"""
        values = []
        for _ in range(duration):
            # Poisson distribution for event count
            events = sum(1 for _ in range(100) if random.random() < lambda_param/100)
            values.append(events)
        return values

class DataGenerator:
    """Generate realistic banking data"""
    
    VIETNAMESE_NAMES = [
        "Nguyen Van A", "Tran Thi B", "Le Van C", "Pham Thi D",
        "Hoang Van E", "Phan Thi F", "Vu Van G", "Dang Thi H",
        "Nguyen Thi Mai", "Tran Van Hung", "Le Thi Lan", "Pham Van Minh"
    ]
    
    VIETNAMESE_CITIES = [
        "Ho Chi Minh", "Ha Noi", "Da Nang", "Hai Phong", "Can Tho",
        "Bien Hoa", "Vung Tau", "Nha Trang", "Hue", "Buon Ma Thuot"
    ]
    
    PHONE_PREFIXES = ["090", "091", "093", "094", "097", "098", "032", "033", "034", "035", "070", "076", "077", "078", "079", "081", "082", "083", "084", "085"]
    
    ISP_RANGES = [
        "113.161", "116.103", "118.69", "171.224", "171.244",
        "14.160", "14.161", "14.162", "27.64", "27.65"
    ]
    
    BANKS = [
        "Vietcombank", "BIDV", "VietinBank", "Agribank", "Techcombank",
        "MB Bank", "ACB", "VPBank", "Sacombank", "TPBank"
    ]
    
    SERVICES = [
        "payment-service", "auth-service", "transfer-service", "account-service",
        "loan-service", "card-service", "notification-service", "kyc-service"
    ]
    
    @staticmethod
    def generate_phone() -> str:
        """Generate valid Vietnamese phone number"""
        prefix = random.choice(DataGenerator.PHONE_PREFIXES)
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(7)])
        return f"{prefix}{suffix}"
    
    @staticmethod
    def generate_account_number() -> str:
        """Generate bank account number"""
        return ''.join([str(random.randint(0, 9)) for _ in range(12)])
    
    @staticmethod
    def generate_ip() -> str:
        """Generate Vietnamese ISP IP address"""
        prefix = random.choice(DataGenerator.ISP_RANGES)
        suffix = f"{random.randint(1, 254)}.{random.randint(1, 254)}"
        return f"{prefix}.{suffix}"
    
    @staticmethod
    def generate_transaction_amount(pattern: str = "normal") -> int:
        """Generate transaction amount based on pattern"""
        if pattern == "normal":
            return int(random.lognormvariate(13, 1.5))  # Mean ~500k VND
        elif pattern == "fraud":
            return random.randint(10_000_000, 50_000_000)  # 10-50M VND
        elif pattern == "micro":
            return random.randint(1_000, 10_000)  # 1-10k VND
        return random.randint(100_000, 1_000_000)
    
    @staticmethod
    def generate_user_data() -> Dict[str, Any]:
        """Generate complete user data"""
        return {
            "user_id": f"USR{random.randint(100000, 999999)}",
            "name": random.choice(DataGenerator.VIETNAMESE_NAMES),
            "phone": DataGenerator.generate_phone(),
            "account": DataGenerator.generate_account_number(),
            "ip_address": DataGenerator.generate_ip(),
            "city": random.choice(DataGenerator.VIETNAMESE_CITIES),
            "bank": random.choice(DataGenerator.BANKS)
        }
    
    @staticmethod
    def generate_service_name() -> str:
        """Generate service name"""
        return random.choice(DataGenerator.SERVICES)

# Storage
generation_jobs: Dict[str, Dict[str, Any]] = {}

@app.get("/")
async def root():
    """Serve the web UI"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pattern Generator</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            h1 { color: #333; border-bottom: 2px solid #2196F3; padding-bottom: 10px; }
            .pattern-demo { margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 8px; }
            button { padding: 10px 20px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
            button:hover { background: #1976D2; }
            .output { background: #263238; color: #aed581; padding: 15px; border-radius: 4px; font-family: monospace; max-height: 400px; overflow-y: auto; }
            .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
            .stat-card { background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center; }
            .stat-value { font-size: 24px; font-weight: bold; color: #1976D2; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Pattern Generator Service</h1>
            <p>Generate realistic patterns and data for anomaly simulation</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" id="jobCount">0</div>
                    <div>Active Jobs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="patternCount">6</div>
                    <div>Pattern Types</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="dataGenerated">0</div>
                    <div>Data Points</div>
                </div>
            </div>
            
            <div class="pattern-demo">
                <h3>Pattern Demonstrations</h3>
                <button onclick="demoPattern('gaussian')">Gaussian Spike</button>
                <button onclick="demoPattern('step')">Step Function</button>
                <button onclick="demoPattern('sawtooth')">Sawtooth</button>
                <button onclick="demoPattern('exponential')">Exponential Decay</button>
                <button onclick="demoPattern('poisson')">Poisson Events</button>
                <button onclick="demoData()">Generate Sample Data</button>
            </div>
            
            <div id="output" class="output"></div>
        </div>
        
        <script>
            async function demoPattern(type) {
                const response = await fetch(`/api/patterns/demo/${type}`);
                const data = await response.json();
                document.getElementById('output').textContent = JSON.stringify(data, null, 2);
            }
            
            async function demoData() {
                const response = await fetch('/api/data/demo');
                const data = await response.json();
                document.getElementById('output').textContent = JSON.stringify(data, null, 2);
            }
            
            async function updateStats() {
                const response = await fetch('/api/jobs');
                const jobs = await response.json();
                document.getElementById('jobCount').textContent = jobs.length;
            }
            
            updateStats();
            setInterval(updateStats, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/generate")
async def generate_patterns(request: GenerationRequest):
    """Generate patterns for a scenario execution"""
    job_id = request.execution_id
    
    # Determine pattern type based on scenario
    pattern_type = "gaussian_spike"
    if "SEC" in request.scenario_id:
        pattern_type = "poisson_events"
    elif "BUS" in request.scenario_id:
        pattern_type = "step_function"
    
    # Generate pattern
    pattern_lib = PatternLibrary()
    if pattern_type == "gaussian_spike":
        values = pattern_lib.gaussian_spike(request.duration, request.rate)
    elif pattern_type == "step_function":
        values = pattern_lib.step_function(request.duration, request.rate)
    elif pattern_type == "poisson_events":
        values = pattern_lib.poisson_events(request.duration, request.rate)
    else:
        values = pattern_lib.sawtooth_pattern(request.duration, request.rate)
    
    # Store job
    generation_jobs[job_id] = {
        "execution_id": request.execution_id,
        "scenario_id": request.scenario_id,
        "pattern_type": pattern_type,
        "values": values,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "job_id": job_id,
        "pattern_type": pattern_type,
        "data_points": len(values),
        "message": "Pattern generation started"
    }

@app.get("/api/patterns/demo/{pattern_type}")
async def demo_pattern(pattern_type: str):
    """Demonstrate a specific pattern type"""
    pattern_lib = PatternLibrary()
    duration = 60
    rate = 100
    
    if pattern_type == "gaussian":
        values = pattern_lib.gaussian_spike(duration, rate)
    elif pattern_type == "step":
        values = pattern_lib.step_function(duration, rate)
    elif pattern_type == "sawtooth":
        values = pattern_lib.sawtooth_pattern(duration, rate)
    elif pattern_type == "exponential":
        values = pattern_lib.exponential_decay(duration, rate)
    elif pattern_type == "poisson":
        values = pattern_lib.poisson_events(duration, rate)
    else:
        raise HTTPException(status_code=400, detail="Unknown pattern type")
    
    return {
        "pattern_type": pattern_type,
        "duration": duration,
        "values": values[:20],  # Return first 20 values for demo
        "statistics": {
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "count": len(values)
        }
    }

@app.get("/api/data/demo")
async def demo_data():
    """Generate sample banking data"""
    data_gen = DataGenerator()
    
    samples = {
        "users": [data_gen.generate_user_data() for _ in range(5)],
        "transactions": [
            {
                "transaction_id": f"TXN{random.randint(1000000, 9999999)}",
                "amount": data_gen.generate_transaction_amount("normal"),
                "currency": "VND",
                "timestamp": datetime.now().isoformat()
            }
            for _ in range(5)
        ],
        "phone_numbers": [data_gen.generate_phone() for _ in range(5)],
        "ip_addresses": [data_gen.generate_ip() for _ in range(5)]
    }
    
    return samples

@app.get("/api/jobs")
async def list_jobs():
    """List all generation jobs"""
    return [
        {
            "job_id": job_id,
            "scenario_id": job["scenario_id"],
            "pattern_type": job["pattern_type"],
            "data_points": len(job["values"]),
            "created_at": job["created_at"]
        }
        for job_id, job in generation_jobs.items()
    ]

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "pattern-generator",
        "active_jobs": len(generation_jobs)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
