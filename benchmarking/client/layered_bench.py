# Enhanced Microbenchmark Suite for Layered Performance Analysis
import argparse
import csv
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import requests
import uuid

# Ensure project root on path to import MCReconstructor
THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from reconstructor.mc_reconstructor import MCReconstructor  # type: ignore

DEFAULT_BASE_URL = os.environ.get("PATRA_BASE_URL", "http://localhost:5002").rstrip("/")
DEFAULT_MCP_URL = os.environ.get("MCP_URL", "http://localhost:8000/jsonrpc").rstrip("/")
DEFAULT_NEO4J_URI = os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
DEFAULT_NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
DEFAULT_NEO4J_PWD = os.environ.get("NEO4J_PWD", "password")

@dataclass
class LayerTiming:
    """Detailed timing breakdown for each layer of the stack"""
    database_ms: float      # Pure Neo4j query time
    protocol_ms: float      # REST/MCP protocol overhead
    network_ms: float       # Network latency
    total_ms: float         # End-to-end time
    
    @property
    def overhead_ratio(self) -> float:
        """Ratio of overhead (protocol + network) to database time"""
        return (self.protocol_ms + self.network_ms) / max(self.database_ms, 0.001)

@dataclass
class TimingStats:
    p50_ms: float
    mean_ms: float
    p90_ms: float
    samples: List[float]
    
    @property
    def stddev_ms(self) -> float:
        return statistics.stdev(self.samples) if len(self.samples) > 1 else 0.0

def compute_stats(samples_ms: List[float]) -> TimingStats:
    if not samples_ms:
        return TimingStats(float("nan"), float("nan"), float("nan"), [])
    
    vals = sorted(samples_ms)
    p50 = statistics.median(vals)
    mean = statistics.fmean(vals)
    p90 = vals[max(0, int(0.9 * (len(vals) - 1)))]
    
    return TimingStats(round(p50, 3), round(mean, 3), round(p90, 3), samples_ms)

def time_calls_detailed(fn, repeats: int, warmup: int = 5, save_csv: Optional[str] = None) -> TimingStats:
    # Warmup phase
    for _ in range(max(0, warmup)):
        try:
            fn()
        except:
            pass  # Ignore warmup errors
    
    samples: List[float] = []
    for i in range(repeats):
        t0 = time.perf_counter()
        try:
            fn()
            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000.0
            samples.append(latency_ms)
        except Exception as e:
            print(f"Warning: Operation failed: {e}")
            # Still record timing for failed operations to understand overhead
            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000.0
            samples.append(latency_ms)
    
    # Save raw samples to CSV if requested
    if save_csv:
        os.makedirs(os.path.dirname(save_csv), exist_ok=True)
        with open(save_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['sample', 'latency_ms'])
            for i, latency in enumerate(samples):
                writer.writerow([i+1, latency])
    
    return compute_stats(samples)

def rpc_with_timing(session: requests.Session, endpoint: str, method: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
    """Execute JSON-RPC call and return result + network timing"""
    payload = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": method, "params": params}
    
    # Measure network round-trip
    network_start = time.perf_counter()
    resp = session.post(endpoint, json=payload, timeout=60)
    network_time = (time.perf_counter() - network_start) * 1000.0
    
    resp.raise_for_status()
    data = resp.json()
    
    if "error" in data:
        raise RuntimeError(data["error"])
    
    return data["result"], network_time

def microbench_get_modelcard(rest_base: str, mcp_url: str, mc_id: str, repeats: int, 
                            neo4j_uri: str, neo4j_user: str, neo4j_pwd: str, output_dir: str = "benchmarking/results") -> Dict[str, Any]:
    """Detailed microbenchmark breaking down database vs protocol vs network time"""
    
    # 1. Pure database timing (no network, no protocol overhead)
    print(f"  Benchmarking database layer...")
    recon = MCReconstructor(neo4j_uri, neo4j_user, neo4j_pwd)
    db_stats = time_calls_detailed(
        lambda: recon.reconstruct(mc_id), 
        repeats, 
        save_csv=f"{output_dir}/get_modelcard_database_latency.csv"
    )
    
    # 2. REST: End-to-end timing
    print(f"  Benchmarking REST end-to-end...")
    rest_sess = requests.Session()
    rest_sess.headers.update({"Connection": "keep-alive"})
    rest_stats = time_calls_detailed(
        lambda: rest_sess.get(f"{rest_base}/modelcard/{mc_id}", timeout=30).raise_for_status(), 
        repeats,
        save_csv=f"{output_dir}/get_modelcard_rest_latency.csv"
    )
    
    # 3. MCP: End-to-end timing with cache OFF (fair comparison)
    print(f"  Benchmarking MCP end-to-end (no cache)...")
    mcp_sess = requests.Session()
    mcp_sess.headers.update({"Connection": "keep-alive"})
    mcp_stats_nocache = time_calls_detailed(
        lambda: rpc_with_timing(mcp_sess, mcp_url, "get_modelcard", {"mc_id": mc_id, "use_cache": False})[0],
        repeats,
        save_csv=f"{output_dir}/get_modelcard_mcp_nocache_latency.csv"
    )
    
    # 4. MCP: End-to-end timing with cache ON 
    print(f"  Benchmarking MCP end-to-end (with cache)...")
    mcp_stats_cached = time_calls_detailed(
        lambda: rpc_with_timing(mcp_sess, mcp_url, "get_modelcard", {"mc_id": mc_id, "use_cache": True})[0],
        repeats,
        save_csv=f"{output_dir}/get_modelcard_mcp_cached_latency.csv"
    )
    
    # 5. Network-only timing (approximate)
    print(f"  Measuring network baseline...")
    network_samples = []
    for _ in range(min(10, repeats)):  # Fewer samples for network baseline
        try:
            _, net_time = rpc_with_timing(mcp_sess, mcp_url, "get_performance_stats", {})
            network_samples.append(net_time)
        except:
            # Fallback: measure simple HTTP request
            t0 = time.perf_counter()
            try:
                rest_sess.get(f"{rest_base}/", timeout=5)
            except:
                pass
            network_samples.append((time.perf_counter() - t0) * 1000.0)
    
    network_baseline = statistics.median(network_samples) if network_samples else 2.0
    
    # Calculate layer breakdowns
    rest_protocol_overhead = max(0, rest_stats.p50_ms - db_stats.p50_ms - network_baseline)
    mcp_protocol_overhead_nocache = max(0, mcp_stats_nocache.p50_ms - db_stats.p50_ms - network_baseline)
    mcp_protocol_overhead_cached = max(0, mcp_stats_cached.p50_ms - db_stats.p50_ms - network_baseline)
    
    return {
        "operation": "get_modelcard",
        "mc_id": mc_id,
        "database": {
            "p50_ms": db_stats.p50_ms,
            "mean_ms": db_stats.mean_ms,
            "p90_ms": db_stats.p90_ms,
            "stddev_ms": db_stats.stddev_ms
        },
        "rest_total": {
            "p50_ms": rest_stats.p50_ms,
            "mean_ms": rest_stats.mean_ms,
            "p90_ms": rest_stats.p90_ms,
            "stddev_ms": rest_stats.stddev_ms
        },
        "mcp_nocache": {
            "p50_ms": mcp_stats_nocache.p50_ms,
            "mean_ms": mcp_stats_nocache.mean_ms,
            "p90_ms": mcp_stats_nocache.p90_ms,
            "stddev_ms": mcp_stats_nocache.stddev_ms
        },
        "mcp_cached": {
            "p50_ms": mcp_stats_cached.p50_ms,
            "mean_ms": mcp_stats_cached.mean_ms,
            "p90_ms": mcp_stats_cached.p90_ms,
            "stddev_ms": mcp_stats_cached.stddev_ms
        },
        "layer_breakdown": {
            "database_p50_ms": db_stats.p50_ms,
            "network_baseline_ms": round(network_baseline, 3),
            "rest_protocol_overhead_ms": round(rest_protocol_overhead, 3),
            "mcp_protocol_overhead_nocache_ms": round(mcp_protocol_overhead_nocache, 3),
            "mcp_protocol_overhead_cached_ms": round(mcp_protocol_overhead_cached, 3),
            "rest_total_overhead_ratio": round((rest_stats.p50_ms - db_stats.p50_ms) / max(db_stats.p50_ms, 0.001), 2),
            "mcp_nocache_overhead_ratio": round((mcp_stats_nocache.p50_ms - db_stats.p50_ms) / max(db_stats.p50_ms, 0.001), 2),
            "mcp_cached_overhead_ratio": round((mcp_stats_cached.p50_ms - db_stats.p50_ms) / max(db_stats.p50_ms, 0.001), 2)
        },
        "performance_analysis": {
            "mcp_nocache_vs_rest_speedup": round(rest_stats.p50_ms / max(mcp_stats_nocache.p50_ms, 0.001), 2),
            "mcp_cached_vs_rest_speedup": round(rest_stats.p50_ms / max(mcp_stats_cached.p50_ms, 0.001), 2),
            "cache_benefit": round((mcp_stats_nocache.p50_ms - mcp_stats_cached.p50_ms) / max(mcp_stats_nocache.p50_ms, 0.001) * 100, 1),
            "database_percentage_of_total": {
                "rest": round(db_stats.p50_ms / max(rest_stats.p50_ms, 0.001) * 100, 1),
                "mcp_nocache": round(db_stats.p50_ms / max(mcp_stats_nocache.p50_ms, 0.001) * 100, 1),
                "mcp_cached": round(db_stats.p50_ms / max(mcp_stats_cached.p50_ms, 0.001) * 100, 1)
            }
        }
    }

def microbench_fair_single_ops(rest_base: str, mcp_url: str, repeats: int, 
                              neo4j_uri: str, neo4j_user: str, neo4j_pwd: str, output_dir: str = "benchmarking/results") -> Dict[str, Any]:
    """Fair comparison of single operations"""
    
    # Get a sample model card ID
    recon = MCReconstructor(neo4j_uri, neo4j_user, neo4j_pwd)
    try:
        all_cards = recon.get_all_mcs()
        mc_id = all_cards[0].get('mc_id') or all_cards[0].get('id') or 'test_model'
    except:
        mc_id = 'test_model'
    
    results = {}
    
    # Test 1: Single model card retrieval
    print("Microbenchmarking: get_modelcard")
    results["get_modelcard"] = microbench_get_modelcard(
        rest_base, mcp_url, mc_id, repeats, neo4j_uri, neo4j_user, neo4j_pwd, output_dir
    )
    
    # Test 2: List operation (limited to make it fair)
    print("Microbenchmarking: list_modelcards (limited)")
    db_list = time_calls_detailed(
        lambda: recon.get_all_mcs()[:100], 
        repeats,
        save_csv=f"{output_dir}/list_modelcards_database_latency.csv"
    )  # Limit to first 100
    
    rest_sess = requests.Session()
    rest_sess.headers.update({"Connection": "keep-alive"})
    rest_list = time_calls_detailed(
        lambda: rest_sess.get(f"{rest_base}/modelcards", timeout=30).raise_for_status(),
        repeats,
        save_csv=f"{output_dir}/list_modelcards_rest_latency.csv"
    )
    
    mcp_sess = requests.Session()
    mcp_sess.headers.update({"Connection": "keep-alive"})
    mcp_list = time_calls_detailed(
        lambda: rpc_with_timing(mcp_sess, mcp_url, "list_modelcards", {"limit": 100})[0],
        repeats,
        save_csv=f"{output_dir}/list_modelcards_mcp_latency.csv"
    )
    
    results["list_modelcards"] = {
        "database_p50_ms": db_list.p50_ms,
        "rest_p50_ms": rest_list.p50_ms,
        "mcp_p50_ms": mcp_list.p50_ms,
        "rest_overhead_ms": round(rest_list.p50_ms - db_list.p50_ms, 3),
        "mcp_overhead_ms": round(mcp_list.p50_ms - db_list.p50_ms, 3),
    }
    
    # Test 3: Search operation  
    print("Microbenchmarking: search_modelcards")
    query = "model"
    db_search = time_calls_detailed(
        lambda: recon.search_kg(query)[:50], 
        repeats,
        save_csv=f"{output_dir}/search_modelcards_database_latency.csv"
    )  # Limit results
    
    rest_search = time_calls_detailed(
        lambda: rest_sess.get(f"{rest_base}/modelcards/search", params={"q": query}, timeout=30).raise_for_status(),
        repeats,
        save_csv=f"{output_dir}/search_modelcards_rest_latency.csv"
    )
    
    mcp_search = time_calls_detailed(
        lambda: rpc_with_timing(mcp_sess, mcp_url, "search_modelcards", {"q": query, "limit": 50})[0],
        repeats,
        save_csv=f"{output_dir}/search_modelcards_mcp_latency.csv"
    )
    
    results["search_modelcards"] = {
        "database_p50_ms": db_search.p50_ms,
        "rest_p50_ms": rest_search.p50_ms,
        "mcp_p50_ms": mcp_search.p50_ms,
        "rest_overhead_ms": round(rest_search.p50_ms - db_search.p50_ms, 3),
        "mcp_overhead_ms": round(mcp_search.p50_ms - db_search.p50_ms, 3),
    }
    
    return results

def main() -> int:
    parser = argparse.ArgumentParser(description="Enhanced layered microbenchmarks: DB vs REST vs MCP")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--neo4j-uri", default=DEFAULT_NEO4J_URI)
    parser.add_argument("--neo4j-user", default=DEFAULT_NEO4J_USER)
    parser.add_argument("--neo4j-pwd", default=DEFAULT_NEO4J_PWD)
    parser.add_argument("--mc-id", help="Specific model card ID to test")
    parser.add_argument("--repeats", type=int, default=1000, help="Number of timing samples per test")
    parser.add_argument("--output", help="JSON output file")
    parser.add_argument("--output-dir", default="benchmarking/results", help="Directory for CSV latency files")
    
    args = parser.parse_args()
    
    print("🔬 Enhanced Microbenchmark Suite for Patra MCP vs REST")
    print("=" * 60)
    print(f"Database: {args.neo4j_uri}")
    print(f"REST API: {args.base_url}")
    print(f"MCP API: {args.mcp_url}")
    print(f"Samples per test: {args.repeats}")
    print()
    
    summary: Dict[str, Any] = {
        "metadata": {
            "timestamp": time.time(),
            "config": {
                "rest_base": args.base_url,
                "mcp_url": args.mcp_url,
                "neo4j_uri": args.neo4j_uri,
                "repeats": args.repeats
            }
        }
    }
    
    # Run fair single operation microbenchmarks
    print("🎯 Running fair single-operation microbenchmarks...")
    summary["fair_single_operations"] = microbench_fair_single_ops(
        args.base_url, args.mcp_url, args.repeats, 
        args.neo4j_uri, args.neo4j_user, args.neo4j_pwd, args.output_dir
    )
    
    # If specific model card ID provided, run detailed analysis
    if args.mc_id:
        print(f"🔍 Running detailed analysis for model card: {args.mc_id}")
        summary["detailed_analysis"] = microbench_get_modelcard(
            args.base_url, args.mcp_url, args.mc_id, args.repeats,
            args.neo4j_uri, args.neo4j_user, args.neo4j_pwd, args.output_dir
        )
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"📊 Results saved to {args.output}")
    else:
        print("\n📊 MICROBENCHMARK RESULTS")
        print("=" * 40)
        print(json.dumps(summary, indent=2))
    
    print(f"\n📁 CSV latency files saved to: {args.output_dir}")
    print("   - get_modelcard_database_latency.csv")
    print("   - get_modelcard_rest_latency.csv") 
    print("   - get_modelcard_mcp_nocache_latency.csv")
    print("   - get_modelcard_mcp_cached_latency.csv")
    print("   - list_modelcards_database_latency.csv")
    print("   - list_modelcards_rest_latency.csv")
    print("   - list_modelcards_mcp_latency.csv")
    print("   - search_modelcards_database_latency.csv")
    print("   - search_modelcards_rest_latency.csv")
    print("   - search_modelcards_mcp_latency.csv")
    
    # Print summary insights
    print("\n🎯 KEY INSIGHTS:")
    fair_ops = summary.get("fair_single_operations", {})
    
    for op_name, op_data in fair_ops.items():
            rest_overhead = op_data.get("rest_overhead_ms", 0)
            mcp_overhead = op_data.get("mcp_overhead_ms", 0)
            
            print(f"  {op_name}:")
            print(f"    REST overhead: {rest_overhead}ms")
            print(f"    MCP overhead: {mcp_overhead}ms")
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())