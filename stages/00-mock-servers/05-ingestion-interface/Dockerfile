FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

COPY app.py .
COPY kinesis_producer.py .

EXPOSE 8004

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8004"]
