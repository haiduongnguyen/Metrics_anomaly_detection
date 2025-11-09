# Stage 03 - Storage Dashboard
# FastAPI service:
# - /health
# - /api/stats (aggregates storage-router and lifecycle-manager)
# - / (HTML UI)
# Env (optional):
# - STORAGE_ROUTER_URL (default http://storage-router:8030)
# - LIFECYCLE_URL (default http://lifecycle-manager:8031)
# - REFRESH_MS (default 2000)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn requests

# Use a real source file to avoid heredoc quoting issues during build
COPY app.py /app/app.py

EXPOSE 8036
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8036"]