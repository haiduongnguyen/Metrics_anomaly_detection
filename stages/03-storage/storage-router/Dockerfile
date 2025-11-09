# Stage 03 - Storage Router Service
# Minimal FastAPI app:
# - Exposes /health, /stats
# - Periodically copies a small batch from transformed logs -> warm bucket
# - Tracks last route timestamp and ticks in Redis
# - Compatible with LocalStack S3

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (no bash/heredoc needed)
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Python deps
RUN pip install --no-cache-dir fastapi uvicorn boto3 redis

# Use source file instead of heredoc to avoid quoting errors
COPY app.py /app/app.py

EXPOSE 8030

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8030"]