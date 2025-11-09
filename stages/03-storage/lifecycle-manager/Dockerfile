# Stage 03 - Lifecycle Manager Service
# - Exposes /health and /stats
# - Periodically transitions objects from WARM -> COLD tiers (simulated)
# - Compatible with LocalStack S3 for local development

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (no heredoc usage)
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Python deps
RUN pip install --no-cache-dir fastapi uvicorn boto3

# Use source file instead of heredoc to avoid quoting errors
COPY app.py /app/app.py

EXPOSE 8031

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8031"]