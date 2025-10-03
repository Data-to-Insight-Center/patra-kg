# Patra Benchmark Client

Run the benchmark against locally running backend services.

## Usage

```bash
# From benchmarking/client
docker-compose up --build

# Results
ls -la ../results
```

Backend expected on:
- REST: http://localhost:5002
- MCP:  http://localhost:8000/jsonrpc

