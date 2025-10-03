Patra MCP Server
=================

This MCP server exposes optimized tools that access the Knowledge Graph directly (no REST):

- `list_modelcards(limit=1000)`: List model cards from Neo4j
- `get_modelcard(mc_id: str)`: Retrieve a single model card by ID
- `search_modelcards(q: str, limit=50)`: Full-text search for model cards
- `batch_get_modelcards(mc_ids: List[str])`: Efficient batch operations
- `workflow_list_and_get(limit=10)`: Combined operations in single call
- `get_performance_stats()`: Session-aware performance monitoring
- `clear_cache()`: Cache management

## Docker Setup (Recommended)

### Quick Start with Docker Compose

```bash
# Start both MCP server and Neo4j
docker-compose up -d

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f mcp-server
```

### Manual Docker Build

```bash
# Build the image
docker build -t patra-mcp-server .

# Run with external Neo4j
docker run -p 8000:8000 \
  -e NEO4J_URI=neo4j://host.docker.internal:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PWD=your_password \
  patra-mcp-server

# Run in stdio mode
docker run -it patra-mcp-server python server.py
```

### Push to Docker Hub

```bash
# Use the provided script (replace with your Docker Hub username)
./push-to-dockerhub.sh your-dockerhub-username

# Or manually:
docker build -t patra-mcp-server .
docker tag patra-mcp-server:latest your-username/patra-mcp-server:latest
docker push your-username/patra-mcp-server:latest
```

### Using from Docker Hub

```bash
# Pull and run from Docker Hub
docker pull your-username/patra-mcp-server:latest
docker run -p 8000:8000 \
  -e NEO4J_URI=neo4j://host.docker.internal:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PWD=your_password \
  your-username/patra-mcp-server:latest
```

## Local Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure Neo4j connection via environment variables (defaults in parentheses):

```bash
export NEO4J_URI=neo4j://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PWD=your_password
```

### Run Options

**HTTP Mode (for testing):**
```bash
python server.py --http --port 8000
```

**Stdio Mode (for MCP clients):**
```bash
python server.py
```

## Environment Variables

- `NEO4J_URI`: Neo4j connection URI (default: `neo4j://localhost:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PWD`: Neo4j password (default: `password`)
- `MCP_MODE`: Server mode - `stdio` or `http` (default: `stdio`)
- `MCP_PORT`: HTTP port when in HTTP mode (default: `8000`)

## Features

- **Batch Operations**: Efficient batch processing for multiple model cards
- **Caching**: In-memory cache with TTL for frequently accessed data
- **Performance Monitoring**: Real-time stats and session tracking
- **Health Checks**: Built-in health monitoring endpoints
- **Flexible Deployment**: Support for both stdio and HTTP modes
