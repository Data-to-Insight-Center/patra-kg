import sys
import logging
import json
import os
import time
from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel
from typing import Any, Dict

# Add project root to Python path for module imports
PROJECT_ROOT = "/app"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils import get_model_card, search_model_cards, close_driver, create_edge

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create FastAPI app
app = FastAPI(
    title="Patra Knowledge Graph API",
    description="API to interact with Patra Knowledge Graph",
    version="1.0.0"
)

@app.get("/")
async def home():
    """Health check endpoint."""
    return {"message": "Patra Knowledge Graph API"}

@app.get("/modelcard/{mc_id}")
async def get_modelcard(mc_id: str, response: Response):
    """
    Get a model card by its ID.

    Args:
        mc_id: The model card ID to retrieve

    Returns:
        Complete model card data or error if not found
    """
    start_time = time.perf_counter()
    model_card = await get_model_card(mc_id)
    end_time = time.perf_counter()
    if model_card is None:
        raise HTTPException(status_code=404, detail=f"Model card {mc_id} not found")
    model_card["database_ms"] = (end_time - start_time) * 1000
    return model_card


@app.post("/edge")
async def create_edge_endpoint(source_node_id: str = Query(...), target_node_id: str = Query(...)):
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
    result = await create_edge(source_node_id, target_node_id)
    end_time = time.perf_counter()
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to create edge")
    result["database_ms"] = (end_time - start_time) * 1000
    return result


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logging.info("Starting Patra Knowledge Graph API")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await close_driver()
    logging.info("Shutting down Patra Knowledge Graph API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)