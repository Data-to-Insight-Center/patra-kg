from mcp.server.fastmcp import FastMCP
import os
import json
import sys
from typing import Any, Dict
import time
import asyncio

# Add project root to Python path for module imports
PROJECT_ROOT = "/app"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils import get_model_card, search_model_cards, create_edge as create_edge_util

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
    if model_card is None:
        return json.dumps({"error": "Model card not found", "database_ms": (end_time - start_time) * 1000})
    model_card["database_ms"] = (end_time - start_time) * 1000
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
    result = await create_edge_util(source_node_id, target_node_id)
    end_time = time.perf_counter()
    if result is None:
        return {"success": False, "error": "Failed to create edge", "database_ms": (end_time - start_time) * 1000}
    result["database_ms"] = (end_time - start_time) * 1000    
    return result



if __name__ == "__main__":
    mcp.run(transport="sse")