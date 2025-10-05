# Optimized Benchmark - Focus on MCP Strengths & Fair Comparison
import argparse
import concurrent.futures
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import requests
import uuid
import csv
from pathlib import Path

DEFAULT_BASE_URL = os.environ.get("PATRA_BASE_URL", "http://localhost:5002")

@dataclass
class TimingResult:
    label: str
    samples_ms: List[float]

    @property
    def p50(self) -> float:
        return statistics.median(self.samples_ms) if self.samples_ms else float("nan")

    @property
    def mean(self) -> float:
        return statistics.fmean(self.samples_ms) if self.samples_ms else float("nan")

    @property
    def p90(self) -> float:
        if not self.samples_ms:
            return float("nan")
        sorted_vals = sorted(self.samples_ms)
        idx = max(0, int(0.9 * (len(sorted_vals) - 1)))
        return sorted_vals[idx]

def _now_ms() -> float:
    return time.perf_counter() * 1000.0

def time_call(fn: Callable[[], Any], repeats: int = 5) -> TimingResult:
    samples: List[float] = []
    label = getattr(fn, "__name__", "call")
    for _ in range(repeats):
        t0 = _now_ms()
        fn()
        t1 = _now_ms()
        samples.append(t1 - t0)
    return TimingResult(label=label, samples_ms=samples)

class PatraRESTOptimized:
    """Optimized REST client with connection pooling"""
    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        # Fair Comparison: Persistent session for connection pooling
        self.session = requests.Session()
        # Configure session for optimal performance
        self.session.headers.update({'Connection': 'keep-alive'})
        
    def warmup(self):
        """Fair Comparison: Warm up connections"""
        try:
            self.session.get(f"{self.base_url}/", timeout=5)
        except:
            pass

    def list_modelcards(self) -> Dict[str, Any]:
        resp = self.session.get(f"{self.base_url}/modelcards", timeout=60)
        resp.raise_for_status()
        return resp.json()

    def get_modelcard(self, mc_id: str) -> Dict[str, Any]:
        resp = self.session.get(f"{self.base_url}/modelcard/{mc_id}", timeout=30)
        resp.raise_for_status()
        return resp.json()

    def search_modelcards(self, query: str) -> List[Dict[str, Any]]:
        resp = self.session.get(f"{self.base_url}/modelcards/search", params={"q": query}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def batch_get_modelcards(self, mc_ids: List[str]) -> List[Dict[str, Any]]:
        """REST: Multiple requests for batch operation"""
        results = []
        for mc_id in mc_ids:
            try:
                result = self.get_modelcard(mc_id)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "mc_id": mc_id})
        return results

class MCPClientOptimized:
    """Enhanced MCP client leveraging protocol strengths"""
    def __init__(self, endpoint: str):
        self.endpoint = endpoint.rstrip("/")
        self.session = requests.Session()
        # Fair Comparison: Persistent HTTP connection
        self.session.headers.update({'Connection': 'keep-alive'})
        self.session_id: Optional[str] = None
        self._initialize_session()

    def warmup(self):
        """Fair Comparison: Session establishment and warmup"""
        if not self.session_id:
            self._initialize_session()

    def _initialize_session(self):
        """Proper MCP session initialization"""
        init_payload = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {"protocolVersion": "2025-01-07", "capabilities": {}},
            "id": "init",
        }
        try:
            resp = self.session.post(self.endpoint, json=init_payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            sid = resp.headers.get("Mcp-Session-Id")
            if not sid:
                sid = (data.get("result") or {}).get("sessionId")
            self.session_id = sid
            print(f"✅ MCP session initialized: {self.session_id}")
        except Exception as e:
            print(f"Warning: MCP session initialization failed: {e}")

    def _rpc(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": str(uuid.uuid4()),
        }
        resp = self.session.post(self.endpoint, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        return data["result"]

    def batch(self, operations: List[Dict[str, Any]]) -> Any:
        """MCP Strength: True batch operations"""
        if not operations:
            return []
        
        if not self.session_id:
            # Fallback to sequential calls
            return [self._rpc(op["method"], op.get("params", {})) for op in operations]
        
        return self._rpc("batch", {"sessionId": self.session_id, "operations": operations})

    def list_modelcards(self) -> Dict[str, Any]:
        return self._rpc("list_modelcards")

    def get_modelcard(self, mc_id: str) -> Dict[str, Any]:
        return self._rpc("get_modelcard", {"mc_id": mc_id})

    def search_modelcards(self, query: str) -> List[Dict[str, Any]]:
        return self._rpc("search_modelcards", {"q": query})

    def batch_get_modelcards(self, mc_ids: List[str]) -> List[Dict[str, Any]]:
        """MCP Strength: Native batch operation in single request"""
        if not mc_ids:
            return []
        return self._rpc("batch_get_modelcards", {"mc_ids": mc_ids})

    def workflow_list_and_get(self, limit: int = 10) -> Dict[str, Any]:
        """MCP Strength: Combined workflow operation"""
        return self._rpc("workflow_list_and_get", {"limit": limit})

def get_sample_ids(rest: PatraRESTOptimized, max_count: int = 1000) -> List[str]:
    """Retrieve up to max_count model card IDs from the REST API.

    Falls back to synthetic IDs if listing fails.
    """
    try:
        all_cards = rest.list_modelcards()
        if isinstance(all_cards, dict):
            ids = list(all_cards.keys())[:max_count]
        elif isinstance(all_cards, list):
            ids = []
            for item in all_cards:
                mc_id = item.get("mc_id") or item.get("id")
                if mc_id:
                    ids.append(mc_id)
                if len(ids) >= max_count:
                    break
        else:
            ids = []
        return ids
    except Exception as e:
        print(f"Could not get sample IDs: {e}")
        return [f"model_{i}" for i in range(min(10, max_count))]

def run_batch_and_workflow_benchmarks(
    rest: PatraRESTOptimized,
    mcp: Optional[MCPClientOptimized],
    repeats: int,
    batch_sizes: List[int],
    workflow_limits: List[int],
) -> Dict[str, List[Dict[str, Any]]]:
    """Run only batch and workflow benchmarks and return structured results.

    Returns a dict with two keys: "batch" and "workflow", each a list of rows.
    """
    results: Dict[str, List[Dict[str, Any]]] = {"batch": [], "workflow": []}

    sample_ids = get_sample_ids(rest, max_count=max(batch_sizes + workflow_limits + [100]))

    # Batch operations
    for batch_size in batch_sizes:
        if batch_size > len(sample_ids):
            continue
        batch_ids = sample_ids[:batch_size]

        def rest_batch() -> Any:
            return rest.batch_get_modelcards(batch_ids)

        row: Dict[str, Any] = {
            "operation": f"Batch Get {batch_size} cards",
            "batch_size": batch_size,
            "repeats": repeats,
        }

        try:
            rest_timing = time_call(rest_batch, repeats=repeats)
            row["rest_p50_ms"] = round(rest_timing.p50, 3)
            row["rest_mean_ms"] = round(rest_timing.mean, 3)
        except Exception as e:
            print(f"REST batch {batch_size} failed: {e}")
            row["rest_p50_ms"] = 0.0
            row["rest_mean_ms"] = 0.0

        if mcp:
            def mcp_batch() -> Any:
                return mcp.batch_get_modelcards(batch_ids)
            try:
                mcp_timing = time_call(mcp_batch, repeats=repeats)
                row["mcp_p50_ms"] = round(mcp_timing.p50, 3)
                row["mcp_mean_ms"] = round(mcp_timing.mean, 3)
            except Exception as e:
                print(f"MCP batch {batch_size} failed: {e}")
                row["mcp_p50_ms"] = 0.0
                row["mcp_mean_ms"] = 0.0
        else:
            row["mcp_p50_ms"] = 0.0
            row["mcp_mean_ms"] = 0.0

        if row["rest_p50_ms"] > 0 and row["mcp_p50_ms"] > 0:
            row["mcp_advantage_pct"] = round(((row["rest_p50_ms"] - row["mcp_p50_ms"]) / row["rest_p50_ms"]) * 100.0, 1)
        else:
            row["mcp_advantage_pct"] = 0.0

        results["batch"].append(row)

    # Workflow operations
    for limit in workflow_limits:
        def rest_workflow() -> Any:
            cards = rest.list_modelcards()
            if isinstance(cards, dict):
                card_ids = list(cards.keys())[:limit]
            else:
                card_ids = [c.get("mc_id") or c.get("id") for c in cards[:limit]]
            card_ids = [i for i in card_ids if i]
            for cid in card_ids:
                try:
                    rest.get_modelcard(cid)
                except Exception:
                    pass

        row_wf: Dict[str, Any] = {
            "operation": f"Workflow: List+Get {limit}",
            "limit": limit,
            "repeats": repeats,
        }

        try:
            rest_timing = time_call(rest_workflow, repeats=repeats)
            row_wf["rest_p50_ms"] = round(rest_timing.p50, 3)
            row_wf["rest_mean_ms"] = round(rest_timing.mean, 3)
        except Exception as e:
            print(f"REST workflow {limit} failed: {e}")
            row_wf["rest_p50_ms"] = 0.0
            row_wf["rest_mean_ms"] = 0.0

        if mcp:
            def mcp_workflow() -> Any:
                return mcp.workflow_list_and_get(limit=limit)
            try:
                mcp_timing = time_call(mcp_workflow, repeats=repeats)
                row_wf["mcp_p50_ms"] = round(mcp_timing.p50, 3)
                row_wf["mcp_mean_ms"] = round(mcp_timing.mean, 3)
            except Exception as e:
                print(f"MCP workflow {limit} failed: {e}")
                row_wf["mcp_p50_ms"] = 0.0
                row_wf["mcp_mean_ms"] = 0.0
        else:
            row_wf["mcp_p50_ms"] = 0.0
            row_wf["mcp_mean_ms"] = 0.0

        if row_wf["rest_p50_ms"] > 0 and row_wf["mcp_p50_ms"] > 0:
            row_wf["mcp_advantage_pct"] = round(((row_wf["rest_p50_ms"] - row_wf["mcp_p50_ms"]) / row_wf["rest_p50_ms"]) * 100.0, 1)
        else:
            row_wf["mcp_advantage_pct"] = 0.0

        results["workflow"].append(row_wf)

    return results

def benchmark_mcp_strengths(rest: PatraRESTOptimized, mcp: Optional[MCPClientOptimized], repeats: int) -> Dict[str, Dict[str, float]]:
    """Test scenarios where MCP should legitimately excel"""
    results: Dict[str, Dict[str, float]] = {}
    
    # Get sample IDs
    try:
        all_cards = rest.list_modelcards()
        if isinstance(all_cards, dict):
            sample_ids = list(all_cards.keys())[:50]
        elif isinstance(all_cards, list):
            sample_ids = [item.get("mc_id") or item.get("id") for item in all_cards[:50]]
        else:
            sample_ids = []
        sample_ids = [sid for sid in sample_ids if sid]
    except Exception as e:
        print(f"Could not get sample IDs: {e}")
        sample_ids = [f"model_{i}" for i in range(10)]
    
    # Scenario 1: Batch Operations (MCP's Native Strength)
    batch_sizes = [5, 10, 25, 50, 100, 200]
    for batch_size in batch_sizes:
        if batch_size <= len(sample_ids):
            batch_ids = sample_ids[:batch_size]
            
            # REST: Multiple individual requests
            def rest_batch():
                return rest.batch_get_modelcards(batch_ids)
            
            try:
                rest_timing = time_call(rest_batch, repeats=repeats)
                results[f"Batch Get {batch_size} cards"] = {"REST": rest_timing.p50}
            except Exception as e:
                print(f"REST batch {batch_size} failed: {e}")
                results[f"Batch Get {batch_size} cards"] = {"REST": 0.0}
            
            # MCP: Single batch request
            if mcp:
                def mcp_batch():
                    return mcp.batch_get_modelcards(batch_ids)
                
                try:
                    mcp_timing = time_call(mcp_batch, repeats=repeats)
                    results[f"Batch Get {batch_size} cards"]["MCP"] = mcp_timing.p50
                except Exception as e:
                    print(f"MCP batch {batch_size} failed: {e}")
                    results[f"Batch Get {batch_size} cards"]["MCP"] = 0.0
    
    # Scenario 2: Workflow Operations (varying limits)
    workflow_limits = [5, 10, 25, 50, 100, 200]
    for limit in workflow_limits:
        def rest_workflow():
            cards = rest.list_modelcards()
            if isinstance(cards, dict):
                card_ids = list(cards.keys())[:limit]
            else:
                card_ids = [c.get("mc_id") or c.get("id") for c in cards[:limit]]
            card_ids = [i for i in card_ids if i]

            for cid in card_ids:
                try:
                    rest.get_modelcard(cid)
                except:
                    pass

        try:
            rest_timing = time_call(rest_workflow, repeats=repeats)
            results[f"Workflow: List+Get {limit}"] = {"REST": rest_timing.p50}
        except Exception as e:
            print(f"REST workflow {limit} failed: {e}")
            results[f"Workflow: List+Get {limit}"] = {"REST": 0.0}

        if mcp:
            def mcp_workflow():
                return mcp.workflow_list_and_get(limit=limit)

            try:
                mcp_timing = time_call(mcp_workflow, repeats=repeats)
                results[f"Workflow: List+Get {limit}"]["MCP"] = mcp_timing.p50
            except Exception as e:
                print(f"MCP workflow {limit} failed: {e}")
                results[f"Workflow: List+Get {limit}"]["MCP"] = 0.0
    
    # Scenario 3: Session-Persistent Multiple Operations
    def rest_multi_ops():
        rest.list_modelcards()
        results = rest.search_modelcards("model")
        if results:
            for result in results[:5]:
                mc_id = result.get("mc_id") or result.get("id")
                if mc_id:
                    try:
                        rest.get_modelcard(str(mc_id))
                    except:
                        pass
    
    try:
        rest_timing = time_call(rest_multi_ops, repeats=repeats)
        results["Multi-ops: List+Search+Get5"] = {"REST": rest_timing.p50}
    except Exception as e:
        print(f"REST multi-ops failed: {e}")
        results["Multi-ops: List+Search+Get5"] = {"REST": 0.0}
    
    if mcp:
        def mcp_multi_ops():
            # Single batch request containing multiple operations
            ops = [
                {"method": "list_modelcards", "params": {}},
                {"method": "search_modelcards", "params": {"q": "model"}},
            ]
            batch_result = mcp.batch(ops)
            
            # Get details for search results
            if len(batch_result) > 1 and batch_result[1]:
                search_results = batch_result[1]
                if isinstance(search_results, list):
                    for result in search_results[:5]:
                        mc_id = result.get("mc_id") or result.get("id") 
                        if mc_id:
                            try:
                                mcp.get_modelcard(str(mc_id))
                            except:
                                pass
        
        try:
            mcp_timing = time_call(mcp_multi_ops, repeats=repeats)
            results["Multi-ops: List+Search+Get5"]["MCP"] = mcp_timing.p50
        except Exception as e:
            print(f"MCP multi-ops failed: {e}")
            results["Multi-ops: List+Search+Get5"]["MCP"] = 0.0
    
    return results

def benchmark_single_operations(rest: PatraRESTOptimized, mcp: Optional[MCPClientOptimized], repeats: int) -> Dict[str, Dict[str, float]]:
    """Fair comparison of basic operations"""
    results: Dict[str, Dict[str, float]] = {}
    
    # Get sample ID
    try:
        all_cards = rest.list_modelcards()
        if isinstance(all_cards, dict):
            sample_id = next(iter(all_cards.keys()))
        elif isinstance(all_cards, list):
            sample_id = all_cards[0].get("mc_id") or all_cards[0].get("id")
        else:
            sample_id = None
    except:
        sample_id = "test_model"
    
    # List operations
    operations = [
        ("List 100 model cards", 100),
        ("List 1000 model cards", 1000),
    ]
    
    for label, n in operations:
        def rest_list():
            cards = rest.list_modelcards()
            if isinstance(cards, dict):
                _ = list(cards.items())[:n]
            else:
                _ = cards[:n]
        
        try:
            rest_timing = time_call(rest_list, repeats=repeats)
            results[label] = {"REST": rest_timing.p50}
        except Exception as e:
            print(f"REST {label} failed: {e}")
            results[label] = {"REST": 0.0}
        
        if mcp:
            def mcp_list():
                cards = mcp.list_modelcards()
                if isinstance(cards, dict):
                    _ = list(cards.items())[:n]
                else:
                    _ = cards[:n]
            
            try:
                mcp_timing = time_call(mcp_list, repeats=repeats)
                results[label]["MCP"] = mcp_timing.p50
            except Exception as e:
                print(f"MCP {label} failed: {e}")
                results[label]["MCP"] = 0.0
    
    # Single get operation
    if sample_id:
        try:
            rest_get = time_call(lambda: rest.get_modelcard(sample_id), repeats=repeats)
            results["Get single model card"] = {"REST": rest_get.p50}
        except Exception as e:
            print(f"REST get single failed: {e}")
            results["Get single model card"] = {"REST": 0.0}
        
        if mcp:
            try:
                mcp_get = time_call(lambda: mcp.get_modelcard(sample_id), repeats=repeats)
                results["Get single model card"]["MCP"] = mcp_get.p50
            except Exception as e:
                print(f"MCP get single failed: {e}")
                results["Get single model card"]["MCP"] = 0.0
    
    # Search operations
    search_tests = [("Search (10 results)", 10), ("Search (50 results)", 50)]
    for label, k in search_tests:
        def rest_search():
            res = rest.search_modelcards("model")
            _ = res[:k]
        
        try:
            rest_timing = time_call(rest_search, repeats=repeats)
            results[label] = {"REST": rest_timing.p50}
        except Exception as e:
            print(f"REST {label} failed: {e}")
            results[label] = {"REST": 0.0}
        
        if mcp:
            def mcp_search():
                res = mcp.search_modelcards("model")
                _ = res[:k]
            
            try:
                mcp_timing = time_call(mcp_search, repeats=repeats)
                results[label]["MCP"] = mcp_timing.p50
            except Exception as e:
                print(f"MCP {label} failed: {e}")
                results[label]["MCP"] = 0.0
    
    return results

def main() -> None:
    parser = argparse.ArgumentParser(description="Optimized MCP vs REST Benchmark")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of REST API")
    parser.add_argument("--mcp-url", help="HTTP JSON-RPC endpoint for optimized MCP server")
    parser.add_argument("--repeats", type=int, default=10, help="Repetitions per measurement")
    args = parser.parse_args()

    print("🚀 Starting Optimized MCP vs REST Benchmark")
    print("=" * 60)

    # Initialize clients
    rest_client = PatraRESTOptimized(args.base_url)
    mcp_client: Optional[MCPClientOptimized] = None
    if args.mcp_url:
        try:
            mcp_client = MCPClientOptimized(args.mcp_url)
        except Exception as e:
            print(f"❌ MCP client initialization failed: {e}")
    
    # Fair Comparison: Warm up both clients
    print("🔥 Warming up connections...")
    rest_client.warmup()
    if mcp_client:
        mcp_client.warmup()
    
    base_dir = Path("/app/results")
    
    # Only Batch and Workflow results
    batch_sizes = [5, 10, 25, 50, 100, 200]
    workflow_limits = [5, 10, 25, 50, 100, 200]

    print("\n🎯 Running Batch and Workflow benchmarks...")
    results = run_batch_and_workflow_benchmarks(
        rest_client,
        mcp_client,
        repeats=args.repeats,
        batch_sizes=batch_sizes,
        workflow_limits=workflow_limits,
    )

    # Write batch results
    with open(base_dir / "batch_operations.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "operation",
            "batch_size",
            "repeats",
            "rest_p50_ms",
            "rest_mean_ms",
            "mcp_p50_ms",
            "mcp_mean_ms",
            "mcp_advantage_pct",
        ])
        for row in results["batch"]:
            writer.writerow([
                row.get("operation"),
                row.get("batch_size"),
                row.get("repeats"),
                row.get("rest_p50_ms"),
                row.get("rest_mean_ms"),
                row.get("mcp_p50_ms"),
                row.get("mcp_mean_ms"),
                row.get("mcp_advantage_pct"),
            ])

    # Write workflow results
    with open(base_dir / "workflow_operations.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "operation",
            "limit",
            "repeats",
            "rest_p50_ms",
            "rest_mean_ms",
            "mcp_p50_ms",
            "mcp_mean_ms",
            "mcp_advantage_pct",
        ])
        for row in results["workflow"]:
            writer.writerow([
                row.get("operation"),
                row.get("limit"),
                row.get("repeats"),
                row.get("rest_p50_ms"),
                row.get("rest_mean_ms"),
                row.get("mcp_p50_ms"),
                row.get("mcp_mean_ms"),
                row.get("mcp_advantage_pct"),
            ])

    print("\n✅ Benchmark complete!")
    print("📊 Results saved to:")
    print("   - batch_operations.csv")
    print("   - workflow_operations.csv")

if __name__ == "__main__":
    sys.exit(main())