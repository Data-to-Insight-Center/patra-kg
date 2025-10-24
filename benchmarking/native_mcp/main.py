from mcp.server.fastmcp import FastMCP
import os
import sys
from typing import Any, Dict, List
from utils import get_model_card, search_model_cards

# Add project root to Python path for module imports
PROJECT_ROOT = "/app"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Create an MCP server
mcp = FastMCP(
    name="Patra MCP Server",
    host="0.0.0.0",  # only used for SSE transport
    port=8050,  # only used for SSE transport (set this to any port)
)

@mcp.tool()
def get_modelcard(mc_id: str) -> Dict[str, Any]:
    """
    Get a model card by its ID.
    
    Args:
        mc_id: The model card ID to retrieve
        
    Returns:
        The model card data as a dictionary
    """
    model_card = get_model_card(mc_id)
    if model_card is None:
        raise ValueError(f"Model card with ID '{mc_id}' not found")
    return model_card


@mcp.tool()
def search_modelcards(q: str) -> List[Dict[str, Any]]:
    """
    Search for model cards using a text query.
    
    Args:
        q: Search query string
        
    Returns:
        List of matching model cards
    """
    results = search_model_cards(q)
    return results


if __name__ == "__main__":
    mcp.run(transport="sse")