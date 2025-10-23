FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN pip install uv

# Copy the whole repo to ensure shared modules like reconstructor are available
COPY .. /app/

# Create timings directory for CSV files
RUN mkdir -p /app/timings && chmod 777 /app/timings

RUN uv venv
RUN uv pip install -r /app/server_mcp/requirements.txt

EXPOSE 8050

CMD ["uv", "run", "server_mcp/main.py"]


