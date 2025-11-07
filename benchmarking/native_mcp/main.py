from mcp.server.fastmcp import FastMCP
import os
import json
import sys
import atexit
from typing import Any, Dict
from utils import get_model_card, search_model_cards, create_edge as create_edge_db, delete_edge as delete_edge_db_func
import time
import asyncio

# Add project root to Python path for module imports
PROJECT_ROOT = "/app"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# In-memory latency tracking
latency_data = []

def write_latency_to_csv():
    """Write accumulated latency data to CSV file on shutdown."""
    if latency_data:
        filename = 'timings/native_mcp/mcp_db_latency.csv'
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
    port=8050,  # only used for SSE transport (set this to any port)
)

@mcp.resource("modelcard://{mc_id}")
async def get_modelcard(mc_id: str) -> str:
    """
    Get a model card by its ID as an MCP resource.

    Resources are for reading existing entities by identifier.
    This follows proper MCP semantics for data retrieval.

    Args:
        mc_id: The model card ID to retrieve

    Returns:
        The model card data as JSON string
    """
    start_time = time.perf_counter()
    model_card = await get_model_card(mc_id)
    end_time = time.perf_counter()
    db_latency = (end_time - start_time) * 1000

    # Store latency in memory
    latency_data.append(db_latency)

    if model_card is None:
        raise ValueError(f"Model card with ID '{mc_id}' not found")

    return json.dumps(model_card)


@mcp.tool()
async def search_modelcards(q: str) -> str:
    """
    Search for model cards using a text query.

    Tools are for performing actions like searches and queries.
    This follows proper MCP semantics for active operations.

    Args:
        q: Search query string

    Returns:
        The search results as JSON string
    """
    start_time = time.perf_counter()
    results = await search_model_cards(q)
    end_time = time.perf_counter()
    db_latency = (end_time - start_time) * 1000

    # Store latency in memory
    latency_data.append(db_latency)

    return json.dumps(results)


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
    result = await create_edge_db(source_node_id, target_node_id)
    end_time = time.perf_counter()
    db_latency = (end_time - start_time) * 1000
    
    # Store latency in memory
    latency_data.append(db_latency)
    
    return result


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
    result = await delete_edge_db_func(source_node_id, target_node_id)
    end_time = time.perf_counter()
    db_latency = (end_time - start_time) * 1000
    
    # Store latency in memory
    latency_data.append(db_latency)
    
    return result


if __name__ == "__main__":
    mcp.run(transport="sse")