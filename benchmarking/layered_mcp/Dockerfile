FROM python:3.12-slim

WORKDIR /app

COPY benchmarking/layered_mcp/requirements.txt /app/requirements.txt
COPY benchmarking/layered_mcp/main.py /app/main.py

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "main.py"]