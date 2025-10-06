import argparse
import csv
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import requests


DEFAULT_MCP_URL = os.environ.get("MCP_URL", "http://localhost:8000/jsonrpc").rstrip("/")


@dataclass
class LatencyStats:
    p50_ms: float
    mean_ms: float
    p90_ms: float


def compute_stats(samples_ms: List[float]) -> LatencyStats:
    if not samples_ms:
        return LatencyStats(float("nan"), float("nan"), float("nan"))
    sorted_vals = sorted(samples_ms)
    p50 = statistics.median(sorted_vals)
    mean = statistics.fmean(sorted_vals)
    p90 = sorted_vals[max(0, int(0.9 * (len(sorted_vals) - 1)))]
    return LatencyStats(round(p50, 3), round(mean, 3), round(p90, 3))


def rpc(session: requests.Session, endpoint: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": "bench", "method": method, "params": params}
    resp = session.post(endpoint, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"]) 
    return data["result"]


def warmup(session: requests.Session, endpoint: str, mc_id: str, count: int) -> None:
    for _ in range(max(0, count)):
        try:
            _ = rpc(session, endpoint, "get_modelcard", {"mc_id": mc_id})
        except Exception:
            pass


def run_sequential(session: requests.Session, endpoint: str, mc_id: str, repeats: int) -> List[float]:
    samples: List[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        _ = rpc(session, endpoint, "get_modelcard", {"mc_id": mc_id})
        t1 = time.perf_counter()
        samples.append((t1 - t0) * 1000.0)
    return samples


def run_concurrent(session: requests.Session, endpoint: str, mc_id: str, repeats: int, workers: int) -> List[float]:
    durations: List[float] = []

    def _one_call() -> float:
        t0 = time.perf_counter()
        _ = rpc(session, endpoint, "get_modelcard", {"mc_id": mc_id})
        t1 = time.perf_counter()
        return (t1 - t0) * 1000.0

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [executor.submit(_one_call) for _ in range(repeats)]
        for fut in as_completed(futures):
            durations.append(fut.result())
    return durations


def save_csv(csv_path: Path, mc_id: str, repeats: int, stats: LatencyStats, raw_samples: List[float]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mc_id", "repeats", "p50_ms", "mean_ms", "p90_ms"])
        w.writerow([mc_id, repeats, stats.p50_ms, stats.mean_ms, stats.p90_ms])

    raw_path = csv_path.parent / (csv_path.stem + "_raw" + csv_path.suffix)
    with raw_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["latency_ms"])
        for v in raw_samples:
            w.writerow([v])


def main() -> int:
    parser = argparse.ArgumentParser(description="Latency microbenchmark for MCP get_modelcard")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL, help="MCP JSON-RPC endpoint (default: %(default)s)")
    parser.add_argument("--mc-id", required=True, help="Model card ID to fetch")
    parser.add_argument("--repeats", type=int, default=50, help="Number of measured requests (default: %(default)s)")
    parser.add_argument("--warmup", type=int, default=5, help="Warmup requests before timing (default: %(default)s)")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent workers (1 for sequential) (default: %(default)s)")
    parser.add_argument("--out-csv", default=str(Path("benchmarking/results/get_modelcard_latency_mcp.csv")), help="Output CSV path (default: %(default)s)")
    args = parser.parse_args()

    endpoint = args.mcp_url
    session = requests.Session()
    session.headers.update({"Connection": "keep-alive"})

    warmup(session, endpoint, args.mc_id, args.warmup)

    if args.workers <= 1:
        samples = run_sequential(session, endpoint, args.mc_id, args.repeats)
    else:
        samples = run_concurrent(session, endpoint, args.mc_id, args.repeats, args.workers)

    stats = compute_stats(samples)
    print(json.dumps({
        "mc_id": args.mc_id,
        "repeats": args.repeats,
        "workers": args.workers,
        "p50_ms": stats.p50_ms,
        "mean_ms": stats.mean_ms,
        "p90_ms": stats.p90_ms,
    }, indent=2))

    save_csv(Path(args.out_csv), args.mc_id, args.repeats, stats, raw_samples=samples)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


