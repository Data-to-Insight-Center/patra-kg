# Patra Benchmarking Suite

A comprehensive benchmarking tool for comparing MCP (Model Context Protocol) vs REST API performance for the Patra Knowledge Graph system.

## 🎯 Features

- **MCP Strength Testing**: Scenarios where MCP should excel (batch operations, workflows)
- **Fair Comparison**: Balanced single-operation comparisons
- **Performance Metrics**: P50, P90, mean response times
- **CSV Output**: Detailed results in CSV format
- **Docker Ready**: Complete containerized setup

## 🐳 Docker Setup (Recommended)

This module is split into two parts:

- `server/`: Backend stack (Neo4j, REST API, MCP server)
- `client/`: Benchmark client that writes CSVs

### Backend Services (`benchmarking/server`)

```bash
cd benchmarking/server
docker-compose up -d

# Check backend health
curl http://localhost:5002/health  # REST API
curl http://localhost:8000/health  # MCP Server
```

### Benchmarking Client (`benchmarking/client`)

```bash
cd benchmarking/client
docker-compose up --build

# View benchmark results
docker-compose logs benchmark

# Check results (saved to benchmarking/results)
ls -la ../results/
```

### Manual Docker Build

```bash
# Build the benchmark image
docker build -t patra-benchmark .

# Run with external services
docker run --rm \
  -e PATRA_BASE_URL=http://host.docker.internal:5002 \
  -e MCP_URL=http://host.docker.internal:8000/jsonrpc \
  -v $(pwd)/results:/app/results \
  patra-benchmark
```

## 🚀 Usage

### Command Line Options

```bash
python main.py [options]

Options:
  --base-url URL        REST API base URL (default: http://localhost:5002)
  --mcp-url URL         MCP JSON-RPC endpoint
  --repeats N           Number of repetitions per test (default: 10)
```

### Environment Variables

- `PATRA_BASE_URL`: REST API base URL
- `MCP_URL`: MCP JSON-RPC endpoint
- `BENCHMARK_REPEATS`: Number of test repetitions
- `OUTPUT_DIR`: Results output directory

## 📊 Benchmark Scenarios

### MCP Strength Tests
- **Batch Operations**: 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000 cards
- **Workflow Operations**: List + Get operations with varying limits
- **Multi-Operations**: Combined list, search, and get operations

### Fair Comparison Tests
- **Single Operations**: List, get, and search operations
- **Response Times**: P50, P90, and mean measurements
- **Connection Pooling**: Optimized for fair comparison

## 📈 Output Files

### `mcp_strengths.csv`
Results where MCP should excel:
- Batch operations performance
- Workflow efficiency
- Multi-operation scenarios

### `fair_comparison.csv`
Balanced comparison results:
- Single operation performance
- Response time differences
- Protocol overhead analysis

## 🔧 Docker Compose Services

### Backend (`server/docker-compose.yml`)
- **neo4j**: Database backend
- **patra-server**: REST API server  
- **patra-mcp-server**: MCP server

### Client (`client/docker-compose.yml`)
- **benchmark**: Benchmarking tool

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Benchmark     │    │   REST Server   │    │   MCP Server    │
│                 │◄──►│                 │    │                 │
│  - Performance  │    │  - Model Cards  │    │  - Batch Ops    │
│  - Metrics      │    │  - Search       │    │  - Workflows    │
│  - CSV Output   │    │  - Single Ops   │    │  - Sessions     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Neo4j       │
                    │   Database      │
                    └─────────────────┘
```

## 🎯 Performance Metrics

- **Response Time**: P50, P90, mean
- **Throughput**: Operations per second
- **Efficiency**: MCP vs REST comparison
- **Scalability**: Batch size performance

## 🔍 Health Checks

All services include health checks:
- **Neo4j**: Cypher query test
- **REST API**: HTTP health endpoint
- **MCP Server**: JSON-RPC health check
- **Benchmark**: Service dependency checks

## 📋 Requirements

- Python 3.11+
- Docker & Docker Compose
- Neo4j 5.11+
- Patra REST Server
- Patra MCP Server

## 🚀 Quick Commands

```bash
# Start backend
cd benchmarking/server && docker-compose up -d

# Run benchmark client
cd ../client && docker-compose up --build

# Run with custom parameters
docker-compose run benchmark python main.py --repeats 20

# View results
docker-compose exec benchmark ls -la /app/results

# Clean up
docker-compose down
cd ../server && docker-compose down -v
```

## 📊 Sample Results

```
🎯 MCP Strength Summary:
   ✅ Batch Get 5 cards: MCP 45.2% faster
   ✅ Batch Get 10 cards: MCP 52.1% faster
   ✅ Workflow: List+Get 25: MCP 38.7% faster
   ✅ Multi-ops: List+Search+Get5: MCP 41.3% faster

🎯 MCP won 4/4 strength-based tests (100.0%)
```
