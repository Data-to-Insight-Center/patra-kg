FROM  --platform=linux/amd64 python:3.9-slim

WORKDIR /app

COPY ../ingester /app/ingester
COPY ../reconstructor /app/reconstructor
COPY server /app/server

RUN pip install -r /app/server/requirements.txt

EXPOSE 5002

ENV PYTHONPATH="${PYTHONPATH}:/app"

ENV OPENAI_API_KEY=''
ENV NEO4J_URI='bolt://locahost:7687'
ENV NEO4J_USER=neo4j
ENV NEO4J_PWD='pwd'
ENV ENABLE_MC_SIMILARITY=False
ENV HF_HUB_USERNAME=''
ENV HF_HUB_TOKEN=''
ENV GH_HUB_USERNAME=''
ENV GH_HUB_TOKEN=''

ENTRYPOINT [ "python", "-u", "/app/server/server.py"]