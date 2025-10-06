import os
import sys
from fastmcp import FastMCP
from typing import List, Dict, Any
    
CURRENT_DIR = os.path.dirname(__file__)
# Two levels up from simple/ to project root
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from reconstructor.mc_reconstructor import MCReconstructor

mcp = FastMCP("patra-mcp-simple")
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PWD", "password")

# Optimized reconstructor with connection pooling
mc_reconstructor = MCReconstructor(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD)

@mcp.tool()
def list_modelcards() -> List[Dict[str, Any]]:
    return mc_reconstructor.get_all_mcs()

@mcp.tool()
def get_modelcard(mc_id: str) -> Dict[str, Any]:
    card = mc_reconstructor.reconstruct(mc_id)
    if card is None:
        raise ValueError(f"Model card '{mc_id}' not found")
    return card

@mcp.tool()
def search_modelcards(q: str) -> List[Dict[str, Any]]:
    return mc_reconstructor.search_kg(q)

# Run the server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=5001)