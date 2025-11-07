from mcp.server.fastmcp import FastMCP
import os
import sys
import atexit
from typing import Any, Dict
import httpx
import asyncio
import time

# Add project root to Python path for module imports
PROJECT_ROOT = "/app"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# In-memory latency tracking
latency_data = []

def write_latency_to_csv():
    """Write accumulated latency data to CSV file on shutdown."""
    if latency_data:
        filename = 'timings/layered_mcp/mcp_rest_latency.csv'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'a') as f:
            for latency in latency_data:
                f.write(f"{latency}\n")

# Register cleanup function
atexit.register(write_latency_to_csv)

# Create an MCP server
mcp = FastMCP(
    name="Patra MCP Server",
    host="0.0.0.0",  # only used for SSE transport
    port=8051,  # only used for SSE transport (set this to any port)
)

REST_API_BASE_URL = os.getenv("REST_API_BASE_URL", "http://rest-server:5002")

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
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REST_API_BASE_URL}/modelcard/{mc_id}")
    end_time = time.perf_counter()
    rest_latency = (end_time - start_time) * 1000

    # Store latency in memory
    latency_data.append(rest_latency)

    # Resources should return string content
    return response.text


@mcp.tool()
async def search_modelcards(q: str) -> str:
    """
    Search for model cards using a text query (via REST layer).

    Tools are for performing actions like searches and queries.
    This MCP server wraps the REST API, demonstrating layered architecture.

    Args:
        q: Search query string

    Returns:
        The search results as JSON string
    """
    start_time = time.perf_counter()
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REST_API_BASE_URL}/search", params={"q": q})
    end_time = time.perf_counter()
    rest_latency = (end_time - start_time) * 1000

    # Store latency in memory
    latency_data.append(rest_latency)

    # Resources should return string content
    return response.text


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
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{REST_API_BASE_URL}/edge",
            json={
                "source_node_id": source_node_id,
                "target_node_id": target_node_id
            }
        )
    end_time = time.perf_counter()
    rest_latency = (end_time - start_time) * 1000
    
    # Store latency in memory
    latency_data.append(rest_latency)
    
    # Handle error responses
    if response.status_code >= 400:
        return {
            "success": False,
            "error": response.json().get("error", f"HTTP {response.status_code}")
        }
    
    return response.json()


@mcp.tool()
async def delete_edge(source_node_id: str, target_node_id: str) -> Dict[str, Any]:
    """
    Delete an edge/relationship between two nodes in the Neo4j graph.
    The relationship type is automatically determined based on the node labels and VALID_LINK_CONSTRAINTS.
    
    Args:
        source_node_id: Neo4j elementId of the source node
        target_node_id: Neo4j elementId of the target node
        
    Returns:
        Dictionary with success status, relationship type, and node information
    """
    start_time = time.perf_counter()
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{REST_API_BASE_URL}/edge",
            json={
                "source_node_id": source_node_id,
                "target_node_id": target_node_id
            }
        )
    end_time = time.perf_counter()
    rest_latency = (end_time - start_time) * 1000
    
    # Store latency in memory
    latency_data.append(rest_latency)
    
    # Handle error responses
    if response.status_code >= 400:
        return {
            "success": False,
            "error": response.json().get("error", f"HTTP {response.status_code}")
        }
    
    return response.json()


if __name__ == "__main__":
    mcp.run(transport="sse")