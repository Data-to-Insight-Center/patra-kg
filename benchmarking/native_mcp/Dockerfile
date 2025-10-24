FROM python:3.12-slim

WORKDIR /app

COPY benchmarking/native_mcp/requirements.txt /app/requirements.txt
COPY benchmarking/native_mcp/main.py /app/main.py
COPY benchmarking/shared_utils.py /app/shared_utils.py

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "main.py"]