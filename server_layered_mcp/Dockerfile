FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY server_layered_mcp/requirements.txt /app/server_layered_mcp/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/server_layered_mcp/requirements.txt

# Copy the rest of the application
COPY server_layered_mcp/ /app/server_layered_mcp/

# Set working directory to server_layered_mcp
WORKDIR /app/server_layered_mcp

# Expose the port
EXPOSE 8051

# Run the MCP server
CMD ["python", "main.py"]

