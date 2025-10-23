from mcp.server.fastmcp import FastMCP
import os
import sys
from typing import Any, Dict, List

# Ensure project root is on sys.path to allow direct imports when running from this directory
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from reconstructor.mc_reconstructor import MCReconstructor
import time
import csv

GET_MC_BENCHMARK_CSV = "/app/timings/mcp/get_modelcard_benchmark.csv"
SEARCH_BENCHMARK_CSV = "/app/timings/mcp/search_benchmark.csv"

# Create an MCP server
mcp = FastMCP(
    name="Patra MCP Server",
    host="0.0.0.0",  # only used for SSE transport
    port=8050,  # only used for SSE transport (set this to any port)
)

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PWD", "password")


# Benchmark flag
BENCHMARK = os.getenv("BENCHMARK", "False").lower() in ("true", "1", "yes")

# Initialize reconstructor
mc_reconstructor = MCReconstructor(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD)

@mcp.tool()
def get_modelcard(mc_id: str) -> Dict[str, Any]:
    """
    Get a model card by its ID.
    
    Args:
        mc_id: The model card ID to retrieve
        
    Returns:
        The model card data as a dictionary
    """
    if BENCHMARK:
        start_time = time.perf_counter()
    model_card = mc_reconstructor.reconstruct(str(mc_id))
    if BENCHMARK:
        elapsed_time = (time.perf_counter() - start_time) * 1000
        with open(GET_MC_BENCHMARK_CSV, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([elapsed_time])
    if model_card is None:
        raise ValueError(f"Model card '{mc_id}' not found")
    return model_card


@mcp.tool()
def search_modelcards(query: str) -> List[Dict[str, Any]]:
    """
    Search for model cards using a text query.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 50)
        
    Returns:
        List of matching model cards
    """
    if BENCHMARK:
        start_time = time.perf_counter()
    results = mc_reconstructor.search_kg(query)
    if BENCHMARK:
        elapsed_time = (time.perf_counter() - start_time) * 1000
        with open(SEARCH_BENCHMARK_CSV, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([elapsed_time])
    return results

if __name__ == "__main__":
    mcp.run(transport="sse")