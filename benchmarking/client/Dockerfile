# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the benchmarking code
COPY main.py .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash benchmark && \
    chown -R benchmark:benchmark /app
USER benchmark

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATRA_BASE_URL=http://patra-server:5002
ENV MCP_URL=http://patra-mcp-server:8000/jsonrpc

# Create results directory
RUN mkdir -p /app/results

# Default command
CMD ["python", "main.py", "--base-url", "http://patra-server:5002", "--mcp-url", "http://patra-mcp-server:8000/jsonrpc", "--repeats", "10"]
