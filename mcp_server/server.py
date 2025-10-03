import os
import sys
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

# Ensure project root is on sys.path to allow direct imports when running from this directory
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from reconstructor.mc_reconstructor import MCReconstructor


mcp = FastMCP("patra-mcp")
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PWD", "password")
mc_reconstructor = MCReconstructor(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD)


@mcp.tool()
def list_modelcards(limit: int = 1000) -> List[Dict[str, Any]]:
    """List model cards directly from the Knowledge Graph."""
    cards = mc_reconstructor.get_all_mcs()
    return cards[:limit]


@mcp.tool()
def get_modelcard(mc_id: str) -> Dict[str, Any]:
    """Get a single model card by ID directly from the Knowledge Graph."""
    result = mc_reconstructor.reconstruct(mc_id)
    if result is None:
        raise ValueError(f"Model card '{mc_id}' not found")
    return result


@mcp.tool()
def search_modelcards(q: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Full-text search across model cards in the Knowledge Graph."""
    results = mc_reconstructor.search_kg(q)
    return results[:limit]


if __name__ == "__main__":
    mcp.run(transport="stdio")


