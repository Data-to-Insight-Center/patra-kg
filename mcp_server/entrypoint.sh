#!/bin/bash

# Entrypoint script for Patra MCP Server
# Provides flexible startup options

set -e

# Default values
MODE=${MCP_MODE:-"stdio"}
PORT=${MCP_PORT:-8000}
NEO4J_URI=${NEO4J_URI:-"neo4j://localhost:7687"}
NEO4J_USER=${NEO4J_USER:-"neo4j"}
NEO4J_PWD=${NEO4J_PWD:-"password"}

# Export environment variables
export NEO4J_URI
export NEO4J_USER
export NEO4J_PWD

echo "🚀 Starting Patra MCP Server..."
echo "📊 Mode: $MODE"
echo "🔗 Neo4j URI: $NEO4J_URI"
echo "👤 Neo4j User: $NEO4J_USER"

# Wait for Neo4j to be ready (if not in stdio mode)
if [ "$MODE" != "stdio" ]; then
    echo "⏳ Waiting for Neo4j to be ready..."
    until python -c "
import os
import sys
sys.path.insert(0, '/app')
from reconstructor.mc_reconstructor import MCReconstructor
try:
    reconstructor = MCReconstructor('$NEO4J_URI', '$NEO4J_USER', '$NEO4J_PWD')
    print('✅ Neo4j connection successful')
except Exception as e:
    print(f'❌ Neo4j connection failed: {e}')
    sys.exit(1)
" 2>/dev/null; do
        echo "⏳ Still waiting for Neo4j..."
        sleep 2
    done
fi

# Start the server based on mode
case "$MODE" in
    "http")
        echo "🌐 Starting HTTP server on port $PORT"
        exec python server.py --http --port "$PORT"
        ;;
    "stdio")
        echo "📡 Starting stdio server"
        exec python server.py
        ;;
    *)
        echo "❌ Unknown mode: $MODE"
        echo "Available modes: stdio, http"
        exit 1
        ;;
esac
