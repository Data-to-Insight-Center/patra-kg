# Use Python 3.9 slim image for compatibility
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY mcp_server/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure (needed for imports from ingester and reconstructor)
COPY . /app/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash mcp && \
    chown -R mcp:mcp /app
USER mcp

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default environment variables
ENV NEO4J_URI=bolt://localhost:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PWD=pwd
ENV ENABLE_MC_SIMILARITY=False
ENV OPENAI_API_KEY=

# Expose port for MCP SSE transport
EXPOSE 8050

# Default command
CMD ["python", "mcp_server/main.py"]

