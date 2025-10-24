import sys
import logging
import os
from fastapi import FastAPI, HTTPException, Query
sys.path.append('/app')
from utils import get_model_card, search_model_cards, close_driver

# Add project root to Python path for module imports
PROJECT_ROOT = "/app"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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
    model_card = get_model_card(mc_id)
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
    
    results = search_model_cards(q)
    return results

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logging.info("Starting Patra Knowledge Graph API")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    close_driver()
    logging.info("Shutting down Patra Knowledge Graph API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)