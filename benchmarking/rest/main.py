import sys
import logging
import os
import time
import atexit
from fastapi import FastAPI, HTTPException, Query
sys.path.append('/app')
from utils import get_model_card, search_model_cards, close_driver

# Add project root to Python path for module imports
PROJECT_ROOT = "/app"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# In-memory latency tracking
latency_data = []

def write_latency_to_csv():
    """Write accumulated latency data to CSV file on shutdown."""
    if latency_data:
        filename = 'timings/rest/rest_db_latency.csv'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'a') as f:
            for latency in latency_data:
                f.write(f"{latency}\n")

# Register cleanup function
atexit.register(write_latency_to_csv)

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
async def get_modelcard(mc_id: str):
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
    db_latency = (end_time - start_time) * 1000

    # Store latency in memory
    latency_data.append(db_latency)

    if model_card is None:
        raise HTTPException(status_code=404, detail="Model card not found")
    return model_card

@app.get("/search")
async def search_modelcards(q: str = Query(..., description="Search query")):
    """
    Search for model cards using a text query.

    Args:
        q: Search query string

    Returns:
        List of matching model cards
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    results = await search_model_cards(q)
    return results

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