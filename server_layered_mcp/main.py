from mcp.server.fastmcp import FastMCP
import os
import httpx
import time
import csv
from typing import Any, Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)

# Create an MCP server
mcp = FastMCP(
    name="Patra Layered MCP Server",
    host="0.0.0.0",
    port=8051,
)

# REST API base URL
REST_API_BASE_URL = os.getenv("REST_API_BASE_URL", "http://rest-server:5002")

# Benchmark flag
BENCHMARK = os.getenv("BENCHMARK", "False").lower() in ("true", "1", "yes")

# Benchmark CSV files
GET_MC_REST_BENCHMARK_CSV = "/app/timings/layered_mcp/get_modelcard_benchmark.csv"
SEARCH_REST_BENCHMARK_CSV = "/app/timings/layered_mcp/search_benchmark.csv"

# HTTP client with timeout
http_client = httpx.Client(timeout=30.0)

def init_benchmark_csv(csv_file, headers):
    """Initialize benchmark CSV file with headers if it doesn't exist."""
    if not BENCHMARK:
        return
    try:
        csv_dir = os.path.dirname(csv_file)
        if csv_dir and not os.path.exists(csv_dir):
            os.makedirs(csv_dir, exist_ok=True)
        
        if not os.path.exists(csv_file):
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    except (PermissionError, OSError) as e:
        logging.warning(f"Cannot initialize benchmark CSV {csv_file}: {e}")

def write_benchmark_csv(csv_file, values):
    """Write benchmark timing to CSV file."""
    if not BENCHMARK:
        return
    try:
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            formatted_values = [f"{v:.2f}" if isinstance(v, float) else v for v in values]
            writer.writerow(formatted_values)
    except (PermissionError, OSError) as e:
        logging.warning(f"Cannot write to benchmark CSV {csv_file}: {e}")

# Initialize benchmark CSV files
init_benchmark_csv(GET_MC_REST_BENCHMARK_CSV, ['latency_ms'])
init_benchmark_csv(SEARCH_REST_BENCHMARK_CSV, ['latency_ms'])


@mcp.tool()
def get_modelcard(mc_id: str) -> Dict[str, Any]:
    """
    Get a model card by its ID from the REST API.
    
    Args:
        mc_id: The model card ID to retrieve
        
    Returns:
        The model card data as a dictionary
    """
    try:
        if BENCHMARK:
            start_time = time.perf_counter()
        
        response = http_client.get(f"{REST_API_BASE_URL}/modelcard/{mc_id}")
        if BENCHMARK:
            elapsed_time = (time.perf_counter() - start_time) * 1000
            write_benchmark_csv(GET_MC_REST_BENCHMARK_CSV, [elapsed_time])
        
        return response.json()
    except httpx.HTTPStatusError as e:
        raise ValueError(f"Error retrieving model card: {e.response.json().get('error', str(e))}")
    except Exception as e:
        raise ValueError(f"Error retrieving model card: {str(e)}")


@mcp.tool()
def search_modelcards(query: str) -> List[Dict[str, Any]]:
    """
    Search for model cards using a text query via the REST API.
    
    Args:
        query: Search query string
        
    Returns:
        List of matching model cards
    """
    try:
        if BENCHMARK:
            start_time = time.perf_counter()
        
        response = http_client.get(f"{REST_API_BASE_URL}/modelcards/search", params={"q": query})        
        if BENCHMARK:
            elapsed_time = (time.perf_counter() - start_time) * 1000
            write_benchmark_csv(SEARCH_REST_BENCHMARK_CSV, [elapsed_time])
        
        return response.json()
    except httpx.HTTPStatusError as e:
        raise ValueError(f"Error searching model cards: {e.response.json().get('error', str(e))}")
    except Exception as e:
        raise ValueError(f"Error searching model cards: {str(e)}")


if __name__ == "__main__":
    mcp.run(transport="sse")

