FROM python:3.12-slim

WORKDIR /app

COPY benchmarking/rest/requirements.txt /app/rest/requirements.txt
COPY benchmarking/rest/main.py /app/rest/main.py
COPY benchmarking/utils.py /app/utils.py

RUN pip install --no-cache-dir -r /app/rest/requirements.txt

CMD ["python", "rest/main.py"]