# Patra Backend Stack

Start Neo4j, REST server, and MCP server for benchmarking.

## Quick Start

```bash
# From benchmarking/server
docker-compose up -d

# Health checks
curl http://localhost:5002/health
curl http://localhost:8000/health
```

## Makefile Workflow (recommended)

```bash
# Start stack and apply constraints automatically (waits for Neo4j to be healthy)
make up

# Re-apply constraints (if you modify constraints.cypher)
make constraints

# Show Neo4j health status
make health

# Tail logs
make logs

# Stop and remove stack and volumes
make down
```

## Constraints

- The Neo4j constraints and indexes are defined in `constraints.cypher` (this folder).
- `make up` will copy this file into the Neo4j container and execute it via `cypher-shell` using the credentials `neo4j/${NEO4J_PWD:-password}`.

## Notes

- Images pulled:
  - `neo4j:5.11-community`
  - `iud2i/patra-server:latest` (REST on :5002)
  - `iud2i/patra-mcp-server:latest` (MCP on :8000)
- Ensure Docker is running and ports 5002/8000/7474/7687 are free.

