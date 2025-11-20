FROM python:3.12-slim

WORKDIR /app

# Install curl for REST benchmarks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY client/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy benchmark script and utilities
COPY client/run_benchmarks.py /app/run_benchmarks.py
COPY client/utils.py /app/utils.py

# Create results directory
RUN mkdir -p /app/results

WORKDIR /app

CMD ["python", "run_benchmarks.py"]

