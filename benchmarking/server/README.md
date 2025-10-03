# Patra Backend Stack

Start Neo4j, REST server, and MCP server for benchmarking.

## Usage

```bash
# From benchmarking/server
docker-compose up -d

# Health checks
curl http://localhost:5002/health
curl http://localhost:8000/health
```

