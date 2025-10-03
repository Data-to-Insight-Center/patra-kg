#!/bin/bash

# Entrypoint script for Patra Benchmarking
# Provides flexible benchmarking options

set -e

# Default values
BASE_URL=${PATRA_BASE_URL:-"http://patra-server:5002"}
MCP_URL=${MCP_URL:-"http://patra-mcp-server:8000/jsonrpc"}
REPEATS=${BENCHMARK_REPEATS:-10}
OUTPUT_DIR=${OUTPUT_DIR:-"/app/results"}

echo "🚀 Starting Patra Benchmarking Suite..."
echo "📊 REST API: $BASE_URL"
echo "🔗 MCP Server: $MCP_URL"
echo "🔄 Repeats: $REPEATS"
echo "📁 Output: $OUTPUT_DIR"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."

# Wait for REST API
echo "🔍 Checking REST API..."
until curl -f "$BASE_URL/health" >/dev/null 2>&1; do
    echo "⏳ Waiting for REST API at $BASE_URL..."
    sleep 5
done
echo "✅ REST API is ready"

# Wait for MCP API
echo "🔍 Checking MCP API..."
until curl -f "$MCP_URL" -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":"test"}' >/dev/null 2>&1; do
    echo "⏳ Waiting for MCP API at $MCP_URL..."
    sleep 5
done
echo "✅ MCP API is ready"

# Run the benchmark
echo "🏁 Starting benchmark..."
python main.py \
    --base-url "$BASE_URL" \
    --mcp-url "$MCP_URL" \
    --repeats "$REPEATS"

# Copy results to output directory
echo "📋 Copying results..."
cp -f *.csv "$OUTPUT_DIR/" 2>/dev/null || true

echo "✅ Benchmark complete!"
echo "📊 Results available in: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"
