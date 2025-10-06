import os
import sys
from typing import Any, Dict, List
import time
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

# Optimized reconstructor with connection pooling
mc_reconstructor = MCReconstructor(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD)

# Performance monitoring
request_stats = {
    "total_requests": 0,
    "batch_requests": 0,
    "cache_hits": 0,
    "avg_response_time": 0.0
}

# Simple in-memory cache for frequently accessed model cards
model_card_cache = {}
CACHE_TTL = 300  # 5 minutes

def get_cached_or_fetch(mc_id: str, fetch_func):
    """Helper function to implement caching"""
    now = time.time()
    if mc_id in model_card_cache:
        cached_data, timestamp = model_card_cache[mc_id]
        if now - timestamp < CACHE_TTL:
            request_stats["cache_hits"] += 1
            return cached_data
    
    # Fetch fresh data
    data = fetch_func(mc_id)
    if data:
        model_card_cache[mc_id] = (data, now)
    return data

@mcp.tool()
def list_modelcards(limit: int = 1000, cached: bool = True) -> List[Dict[str, Any]]:
    """Optimized list with caching support"""
    start_time = time.time()
    request_stats["total_requests"] += 1
    
    cards = mc_reconstructor.get_all_mcs()
    result = cards[:limit]
    
    # Update performance stats
    end_time = time.time()
    request_stats["avg_response_time"] = (
        request_stats["avg_response_time"] * (request_stats["total_requests"] - 1) + 
        (end_time - start_time) * 1000
    ) / request_stats["total_requests"]
    
    return result

@mcp.tool()
def get_modelcard(mc_id: str, use_cache: bool = True) -> Dict[str, Any]:
    """Optimized get with caching"""
    start_time = time.time()
    request_stats["total_requests"] += 1
    
    if use_cache:
        result = get_cached_or_fetch(mc_id, lambda id: mc_reconstructor.reconstruct(id))
    else:
        result = mc_reconstructor.reconstruct(mc_id)
    
    if result is None:
        raise ValueError(f"Model card '{mc_id}' not found")
    
    # Update performance stats
    end_time = time.time()
    request_stats["avg_response_time"] = (
        request_stats["avg_response_time"] * (request_stats["total_requests"] - 1) + 
        (end_time - start_time) * 1000
    ) / request_stats["total_requests"]
    
    return result

@mcp.tool()
def search_modelcards(q: str, limit: int = 50, use_cache: bool = False) -> List[Dict[str, Any]]:
    """Optimized search"""
    start_time = time.time()
    request_stats["total_requests"] += 1
    
    results = mc_reconstructor.search_kg(q)
    result = results[:limit]
    
    # Update performance stats
    end_time = time.time()
    request_stats["avg_response_time"] = (
        request_stats["avg_response_time"] * (request_stats["total_requests"] - 1) + 
        (end_time - start_time) * 1000
    ) / request_stats["total_requests"]
    
    return result

@mcp.tool()
def batch_get_modelcards(mc_ids: List[str], use_cache: bool = True) -> List[Dict[str, Any]]:
    """MCP Strength: Efficient batch operations in single request"""
    start_time = time.time()
    request_stats["total_requests"] += 1
    request_stats["batch_requests"] += 1
    
    results = []
    for mc_id in mc_ids:
        try:
            if use_cache:
                result = get_cached_or_fetch(mc_id, lambda id: mc_reconstructor.reconstruct(id))
            else:
                result = mc_reconstructor.reconstruct(mc_id)
            if result:
                results.append(result)
        except Exception as e:
            # Continue processing other IDs, add error marker
            results.append({"error": str(e), "mc_id": mc_id})
    
    # Update performance stats
    end_time = time.time()
    request_stats["avg_response_time"] = (
        request_stats["avg_response_time"] * (request_stats["total_requests"] - 1) + 
        (end_time - start_time) * 1000
    ) / request_stats["total_requests"]
    
    return results

@mcp.tool()
def get_performance_stats() -> Dict[str, Any]:
    """MCP Strength: Session-aware performance monitoring"""
    return {
        "total_requests": request_stats["total_requests"],
        "batch_requests": request_stats["batch_requests"],
        "batch_percentage": request_stats["batch_requests"] / max(request_stats["total_requests"], 1) * 100,
        "cache_hits": request_stats["cache_hits"],
        "cache_hit_rate": request_stats["cache_hits"] / max(request_stats["total_requests"], 1) * 100,
        "avg_response_time_ms": request_stats["avg_response_time"],
        "cached_items": len(model_card_cache)
    }

@mcp.tool()
def clear_cache() -> Dict[str, str]:
    """Clear the model card cache"""
    global model_card_cache
    cleared_count = len(model_card_cache)
    model_card_cache.clear()
    return {"message": f"Cleared {cleared_count} cached items"}

@mcp.tool()
def workflow_list_and_get(limit: int = 10) -> Dict[str, Any]:
    """MCP Strength: Combined operations in single session call"""
    start_time = time.time()
    request_stats["total_requests"] += 1
    
    # Get list first
    cards = mc_reconstructor.get_all_mcs()
    card_list = cards[:limit]
    
    # Get detailed info for each
    detailed_cards = []
    for card_summary in card_list:
        mc_id = card_summary.get('mc_id') or card_summary.get('id')
        if mc_id:
            detailed = get_cached_or_fetch(mc_id, lambda id: mc_reconstructor.reconstruct(id))
            if detailed:
                detailed_cards.append(detailed)
    
    # Update performance stats
    end_time = time.time()
    request_stats["avg_response_time"] = (
        request_stats["avg_response_time"] * (request_stats["total_requests"] - 1) + 
        (end_time - start_time) * 1000
    ) / request_stats["total_requests"]
    
    return {
        "summary_count": len(card_list),
        "detailed_count": len(detailed_cards),
        "cards": detailed_cards,
        "execution_time_ms": (end_time - start_time) * 1000
    }

if __name__ == "__main__":
    import argparse
    import traceback
    import sys

    parser = argparse.ArgumentParser(description="Optimized Patra MCP Server")
    parser.add_argument("--http", action="store_true", help="Serve JSON-RPC over HTTP on :8000")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default 8000)")
    args = parser.parse_args()

    if args.http:
        from flask import Flask, request, jsonify

        app = Flask(__name__)

        # Map method names to tool functions manually
        TOOLS = {
            "list_modelcards": list_modelcards,
            "get_modelcard": get_modelcard,
            "search_modelcards": search_modelcards,
            "batch_get_modelcards": batch_get_modelcards,  # NEW: Batch operation
            "workflow_list_and_get": workflow_list_and_get,  # NEW: Combined workflow
            "get_performance_stats": get_performance_stats,  # NEW: Performance monitoring
            "clear_cache": clear_cache,  # NEW: Cache management
        }

        import uuid
        sessions: Dict[str, Dict[str, Any]] = {}

        def new_session() -> str:
            sid = str(uuid.uuid4())
            sessions[sid] = {
                "created_at": time.time(),
                "request_count": 0,
                "last_access": time.time()
            }
            return sid

        @app.route("/health")
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "sessions": len(sessions),
                "performance": get_performance_stats()
            })

        @app.post("/jsonrpc")
        def jsonrpc():
            req = request.get_json(force=True)
            rid = req.get("id")
            start_time = time.time()
            
            try:
                method = req["method"]
                params = req.get("params", {})
                
                if method == "initialize":
                    sid = new_session()
                    result = {
                        "sessionId": sid, 
                        "capabilities": {
                            "batch": True,
                            "caching": True,
                            "workflows": True,
                            "performance_monitoring": True
                        }
                    }
                elif method == "batch":
                    # MCP Strength: Efficient batch processing
                    sid = params.get("sessionId")
                    ops = params.get("operations", [])
                    if sid not in sessions:
                        raise ValueError("Invalid sessionId")
                    
                    # Update session stats
                    sessions[sid]["request_count"] += 1
                    sessions[sid]["last_access"] = time.time()
                    
                    batch_results = []
                    for op in ops:
                        op_start = time.time()
                        m = op.get("method")
                        p = op.get("params", {})
                        if m not in TOOLS:
                            batch_results.append({"error": f"unknown method {m}"})
                        else:
                            try:
                                op_result = TOOLS[m](**p)
                                batch_results.append(op_result)
                            except Exception as e:
                                batch_results.append({"error": str(e)})
                        op_end = time.time()
                        
                    result = {
                        "results": batch_results,
                        "batch_size": len(ops),
                        "total_time_ms": (time.time() - start_time) * 1000,
                        "session_id": sid
                    }
                else:
                    if method not in TOOLS:
                        raise ValueError("Unknown method")
                    result = TOOLS[method](**params)
                
                response_time = (time.time() - start_time) * 1000
                return jsonify({
                    "jsonrpc": "2.0", 
                    "result": result, 
                    "id": rid,
                    "_meta": {
                        "response_time_ms": response_time,
                        "server": "patra-mcp-optimized"
                    }
                })
                
            except Exception as exc:
                traceback.print_exc()
                return jsonify({
                    "jsonrpc": "2.0", 
                    "error": {
                        "code": -32000, 
                        "message": str(exc),
                        "response_time_ms": (time.time() - start_time) * 1000
                    }, 
                    "id": rid
                })

        print(f"🚀 Optimized MCP HTTP server running on 0.0.0.0:{args.port}")
        print(f"✨ Features: Batch operations, Caching, Workflows, Performance monitoring")
        print(f"🔍 Health check: http://localhost:{args.port}/health")
        app.run(host="0.0.0.0", port=args.port, threaded=True)
    else:
        mcp.run(transport="stdio")