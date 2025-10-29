# Minimal Banking Mock Server Deployment

## 🚀 Quick Start Options

### Option 1: Local Docker Compose (Recommended for Development)
```bash
cd stages/00-mock-servers

# Start the server
./run.sh

# View logs
./run.sh logs

# Stop the server
./run.sh stop
```

### Option 2: AWS EC2 (Production)
```bash
cd stages/config

# Use minimal Terraform files
terraform apply -var-file=terraform.tfvars \
  -var-file=variables-minimal.tf \
  -var-file=outputs-minimal.tf
```

## 📁 File Structure

### Essential Files (Keep These)
```
stages/
├── 00-mock-servers/
│   ├── app.py                    # ✅ Main application
│   ├── config.yaml              # ✅ Configuration
│   ├── docker-compose.yml       # ✅ Docker setup
│   ├── Dockerfile               # ✅ Container definition
│   ├── run.sh                   # ✅ Quick start script
│   └── requirements.txt         # ✅ Dependencies
└── config/
    ├── main-minimal.tf          # ✅ Minimal AWS setup
    ├── variables-minimal.tf     # ✅ AWS variables
    ├── outputs-minimal.tf       # ✅ AWS outputs
    └── user-data.sh             # ✅ EC2 setup script
```

### Files You Can Remove
```
stages/
├── config/
    ├── main.tf                  # ❌ Complex AWS setup
    ├── variables.tf             # ❌ Complex variables
    ├── outputs.tf               # ❌ Complex outputs
├── deploy.sh                   # ❌ Complex deployment script
└── Other directories/          # ❌ Unused stages
```

## 🎯 What to Keep vs Remove

### ✅ **KEEP** - Essential for Functionality
- `app.py` - Core mock server
- `config.yaml` - Server configuration  
- `docker-compose.yml` - Local deployment
- `Dockerfile` - Container definition
- `run.sh` - Quick start script
- `user-data.sh` - AWS EC2 setup (if you want cloud deployment)

### ❌ **REMOVE** - Redundant/Complex
- Complex Terraform files (`main.tf`, `variables.tf`, `outputs.tf`)
- Deployment scripts (`deploy.sh`)
- Unused stage directories (`01-ingestion`, `02-etl`, etc.)
- Documentation files (if you want minimal setup)

## 🔧 Minimal AWS Deployment

If you want AWS capability with minimal files:

1. **Use the minimal Terraform files:**
   ```bash
   cd stages/config
   terraform init
   terraform apply -var-file=variables-minimal.tf
   ```

2. **Or manually deploy to EC2:**
   - Launch EC2 instance
   - Install Docker
   - Run: `docker run -d -p 8000:8000 banking-mock-server`

## 📦 What You Get

### **Local Setup** (Docker Compose)
- ✅ Mock server with 16 anomaly scenarios
- ✅ JSON log output (10 logs/sec)
- ✅ REST API control
- ✅ Health checks
- ✅ Easy start/stop

### **AWS Setup** (Minimal Terraform)
- ✅ EC2 t3.micro instance
- ✅ Docker container deployment
- ✅ Security group configuration
- ✅ Auto-start on boot

## 🎯 Recommendation

**For most users:** Keep only the `00-mock-servers` directory and use Docker Compose locally.

**For production:** Keep the minimal Terraform files in `config/` for AWS deployment.

The `user-data.sh` is only necessary if you want automated EC2 deployment. For local use, you can remove it.
