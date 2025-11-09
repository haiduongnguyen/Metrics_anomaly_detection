FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh --dry-run && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/* && \
    rm get-docker.sh

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scheduler script
COPY scheduler.py .

# Create state directory
RUN mkdir -p /app/state

# Make script executable
RUN chmod +x scheduler.py

CMD ["python", "-u", "scheduler.py"]
