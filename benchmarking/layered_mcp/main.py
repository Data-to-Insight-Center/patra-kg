from mcp.server.fastmcp import FastMCP
import os
import sys
from typing import Any, Dict
import httpx
import asyncio
import time
import json

# Add project root to Python path for module imports
PROJECT_ROOT = "/app"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Create an MCP server
mcp = FastMCP(
    name="Patra MCP Server",
    host="0.0.0.0",  # only used for SSE transport
    port=8051,  # only used for SSE transport (set this to any port)
)

REST_API_BASE_URL = os.getenv("REST_API_BASE_URL", "http://rest-server:5002")

# Shared HTTP client instance for connection pooling and reuse
_http_client: httpx.AsyncClient | None = None

async def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=1000000.0,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
    return _http_client

@mcp.resource("modelcard://{mc_id}")
async def get_modelcard(mc_id: str) -> str:
    """
    Get a model card by its ID as an MCP resource (via REST layer).

    Resources are for reading existing entities by identifier.
    This MCP server wraps the REST API, demonstrating layered architecture.

    Args:
        mc_id: The model card ID to retrieve

    Returns:
        The model card data as JSON string
    """
    start_time = time.perf_counter()
    client = await get_http_client()
    response = await client.get(f"{REST_API_BASE_URL}/modelcard/{mc_id}")
    end_time = time.perf_counter()
    response.raise_for_status()  # Raise exception for bad status codes
    model_card = response.json()  # Parse JSON response
    if model_card is None:
        return json.dumps({"error": "Model card not found", "rest_ms": (end_time - start_time) * 1000})
    model_card["rest_ms"] = (end_time - start_time) * 1000 - model_card["database_ms"]
    return json.dumps(model_card)


@mcp.tool()
async def create_edge(source_node_id: str, target_node_id: str) -> Dict[str, Any]:
    """
    Create an edge/relationship between two nodes in the Neo4j graph.
    The relationship type is automatically determined based on the node labels and VALID_LINK_CONSTRAINTS.
    
    Args:
        source_node_id: Neo4j elementId of the source node
        target_node_id: Neo4j elementId of the target node
        
    Returns:
        Dictionary with success status, relationship type, and node information
    """
    start_time = time.perf_counter()
    client = await get_http_client()
    response = await client.post(
        f"{REST_API_BASE_URL}/edge",
        params={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id
        }
    )
    end_time = time.perf_counter()
    response.raise_for_status()  # Raise exception for bad status codes
    result = response.json()  # Parse JSON response
    if result is None:
        return {"success": False, "error": "Failed to create edge", "rest_ms": (end_time - start_time) * 1000}
    result["rest_ms"] = (end_time - start_time) * 1000 - result["database_ms"]
    return result

# Cleanup function for shutdown
async def cleanup_http_client():
    """Close the HTTP client on shutdown."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None

# Register cleanup on MCP server shutdown if possible
# Note: FastMCP may not have explicit shutdown hooks, but the client will be cleaned up on process exit


if __name__ == "__main__":
    mcp.run(transport="sse")