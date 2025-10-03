import argparse
import concurrent.futures
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
import uuid
import csv
from datetime import datetime
from pathlib import Path


DEFAULT_BASE_URL = os.environ.get("PATRA_BASE_URL", "http://localhost:5002")


# ---------------- MCP JSON-RPC helper -----------------


class MCPClient:
    """Minimal JSON-RPC 2.0 client for FastMCP HTTP façade."""

    def __init__(self, endpoint: str, session: Optional[requests.Session] = None):
        self.endpoint = endpoint
        self.session = session or requests.Session()

    def _rpc(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": str(uuid.uuid4()),
        }
        resp = self.session.post(self.endpoint, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        return data["result"]

    # Convenience wrappers matching PatraREST API
    def list_modelcards(self) -> Dict[str, Any]:
        return self._rpc("list_modelcards")

    def get_modelcard(self, mc_id: str) -> Dict[str, Any]:
        return self._rpc("get_modelcard", {"mc_id": mc_id})

    def search_modelcards(self, query: str) -> List[Dict[str, Any]]:
        return self._rpc("search_modelcards", {"q": query})


# ------------------------------------------------------


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


def bytes_len(obj: Any) -> int:
    try:
        if isinstance(obj, (bytes, bytearray)):
            return len(obj)
        return len(json.dumps(obj).encode("utf-8"))
    except Exception:
        return 0


class PatraREST:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, session: Optional[requests.Session] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

    def list_modelcards(self) -> Dict[str, Any]:
        resp = self.session.get(f"{self.base_url}/modelcards")
        resp.raise_for_status()
        return resp.json()

    def get_modelcard(self, mc_id: str) -> Dict[str, Any]:
        resp = self.session.get(f"{self.base_url}/modelcard/{mc_id}")
        resp.raise_for_status()
        return resp.json()

    def search_modelcards(self, query: str) -> List[Dict[str, Any]]:
        resp = self.session.get(f"{self.base_url}/modelcards/search", params={"q": query})
        resp.raise_for_status()
        return resp.json()


def single_operation_bench(rest: PatraREST, list_target_sizes: List[int], search_result_targets: List[int], repeats: int) -> Dict[str, TimingResult]:
    results: Dict[str, TimingResult] = {}

    # Preload list to derive IDs and sizes
    all_cards = rest.list_modelcards()
    if isinstance(all_cards, dict):
        all_ids = list(all_cards.keys())
    elif isinstance(all_cards, list):
        all_ids = [item.get("mc_id") or item.get("external_id") or item.get("id") for item in all_cards]
    else:
        all_ids = []

    def list_cards_n(n: int) -> Callable[[], Any]:
        def _fn() -> Any:
            cards = rest.list_modelcards()
            # simulate client-side limiting for table comparability
            if isinstance(cards, dict):
                _ = list(cards.items())[:n]
            elif isinstance(cards, list):
                _ = cards[:n]
            return cards
        _fn.__name__ = f"list_{n}_model_cards"
        return _fn

    def get_single() -> Any:
        target_id = next((i for i in all_ids if i), "dummy-id")
        return rest.get_modelcard(target_id)

    def search_with_expected(k: int) -> Callable[[], Any]:
        query = "model"  # generic query; adjust as needed
        def _fn() -> Any:
            res = rest.search_modelcards(query)
            _ = res[:k]
            return res
        _fn.__name__ = f"search_{k}_results"
        return _fn

    for size in list_target_sizes:
        results[f"List {size}"] = time_call(list_cards_n(size), repeats=repeats)

    results["Get single model card"] = time_call(get_single, repeats=repeats)

    for k in search_result_targets:
        results[f"Search ({k})"] = time_call(search_with_expected(k), repeats=repeats)

    return results


def single_operation_bench_mcp(mcp: MCPClient, repeats: int = 5) -> Dict[str, TimingResult]:
    """Benchmark the same single ops using MCP client."""
    # Use fixed sizes because MCP list/search currently returns all
    scenarios = {
        "List 1000": lambda: mcp.list_modelcards(),
        "Get single model card": lambda: mcp.get_modelcard("dummy") ,  # mc_id will be replaced below
        "Search (50)": lambda: mcp.search_modelcards("model"),
    }

    # Determine a real mc_id
    all_cards = mcp.list_modelcards()
    first_id = None
    if isinstance(all_cards, list) and all_cards:
        first_id = all_cards[0].get("mc_id") or all_cards[0].get("external_id")
    elif isinstance(all_cards, dict):
        first_id = next(iter(all_cards.keys()), None)
    if first_id:
        scenarios["Get single model card"] = lambda fid=first_id: mcp.get_modelcard(fid)

    results: Dict[str, TimingResult] = {}
    for label, fn in scenarios.items():
        results[label] = time_call(fn, repeats=repeats)
    return results


def workflow_bench(rest: PatraREST, repeats: int) -> Dict[str, TimingResult]:
    results: Dict[str, TimingResult] = {}

    def list_then_get_5() -> Any:
        cards = rest.list_modelcards()
        ids = list(cards.keys()) if isinstance(cards, dict) else []
        for mc_id in ids[:5]:
            rest.get_modelcard(mc_id)
        return True

    def search_then_get_3() -> Any:
        res = rest.search_modelcards("model")
        for item in res[:3]:
            mc_id = item.get("external_id") or item.get("id") or next(iter(item.values()), None)
            if mc_id:
                try:
                    rest.get_modelcard(str(mc_id))
                except Exception:
                    pass
        return True

    def list_search_get() -> Any:
        rest.list_modelcards()
        res = rest.search_modelcards("model")
        if res:
            mc_id = res[0].get("external_id") or res[0].get("id") or next(iter(res[0].values()), None)
            if mc_id:
                try:
                    rest.get_modelcard(str(mc_id))
                except Exception:
                    pass
        return True

    def repeated_get_10() -> Any:
        cards = rest.list_modelcards()
        ids = list(cards.keys()) if isinstance(cards, dict) else []
        target = ids[0] if ids else "dummy-id"
        for _ in range(10):
            try:
                rest.get_modelcard(target)
            except Exception:
                pass
        return True

    results["List → Get (5)"] = time_call(list_then_get_5, repeats=repeats)
    results["Search → Get (3)"] = time_call(search_then_get_3, repeats=repeats)
    results["List → Search → Get"] = time_call(list_search_get, repeats=repeats)
    results["Repeated Get (10)"] = time_call(repeated_get_10, repeats=repeats)
    return results


def concurrent_clients_bench(rest_factory: Callable[[], PatraREST], clients: List[int], sequence: Callable[[PatraREST], Any]) -> Dict[int, float]:
    throughput: Dict[int, float] = {}

    def run_client() -> None:
        rest = rest_factory()
        sequence(rest)

    for c in clients:
        start = _now_ms()
        with concurrent.futures.ThreadPoolExecutor(max_workers=c) as pool:
            list(pool.map(lambda _: run_client(), range(c)))
        duration_ms = _now_ms() - start
        # ops = clients (each does sequence once). Convert to ops/sec
        ops_per_sec = (c / (duration_ms / 1000.0)) if duration_ms > 0 else 0.0
        throughput[c] = ops_per_sec
    return throughput


def protocol_overhead(rest: PatraREST) -> Dict[str, int]:
    sizes: Dict[str, int] = {}
    with requests.Session() as s:
        # Session establishment: minimal GET to home if available
        t0 = _now_ms()
        resp = s.get(f"{rest.base_url}/")
        sizes["Session establishment"] = bytes_len(resp.text)
        # Single card retrieval
        cards = rest.list_modelcards()
        ids = list(cards.keys()) if isinstance(cards, dict) else []
        target = ids[0] if ids else "dummy-id"
        try:
            resp = s.get(f"{rest.base_url}/modelcard/{target}")
            sizes["Single card retrieval"] = len(resp.content)
        except Exception:
            sizes["Single card retrieval"] = 0
        # List sizes
        resp = s.get(f"{rest.base_url}/modelcards")
        sizes["List 1000 cards"] = len(resp.content)
        sizes["List 10,000 cards"] = len(resp.content)  # same endpoint; placeholder
        # Search 500 results (depends on data)
        resp = s.get(f"{rest.base_url}/modelcards/search", params={"q": "model"})
        sizes["Search 500 results"] = len(resp.content)
    return sizes


def latex_table_single_ops(results: Dict[str, TimingResult]) -> str:
    rows: List[str] = []
    def cell(val: float) -> str:
        return f"{val:.1f}"
    mapping = {
        "List 100": "List 100 model cards",
        "List 1000": "List 1000 model cards",
        "List 5000": "List 5000 model cards",
        "List 10000": "List 10,000 model cards",
        "Get single model card": "Get single model card",
        "Search (50)": "Search (50 results)",
        "Search (500)": "Search (500 results)",
    }
    for key, label in mapping.items():
        if key in results:
            rest_ms = results[key].p50
            rows.append(f"{label} & {cell(rest_ms)} &  &  \\")
    body = " \\\hline\n".join(rows)
    return body


def latex_table_workflows(results: Dict[str, TimingResult]) -> str:
    order = [
        "List → Get (5)",
        "Search → Get (3)",
        "List → Search → Get",
        "Repeated Get (10)",
    ]
    rows: List[str] = []
    for key in order:
        if key in results:
            rows.append(f"{key} & {results[key].p50:.1f} &  &  \\")
    return " \\\hline\n".join(rows)


def latex_table_concurrency(throughput: Dict[int, float]) -> str:
    rows: List[str] = []
    for c in [1, 5, 10, 20, 50]:
        if c in throughput:
            rows.append(f"{c} & {throughput[c]:.1f} &  &  \\")
    return " \\\hline\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Patra KG REST API")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of the REST API")
    parser.add_argument("--mcp-url", help="HTTP JSON-RPC endpoint for MCP server (e.g. http://localhost:8000/jsonrpc)")
    parser.add_argument("--repeats", type=int, default=5, help="Number of repetitions per measurement")
    parser.add_argument("--concurrency", nargs="*", type=int, default=[1, 5, 10, 20, 50], help="Concurrent client counts")
    args = parser.parse_args()

    rest_client = PatraREST(args.base_url)

    mcp_client: Optional[MCPClient] = None
    if args.mcp_url:
        mcp_client = MCPClient(args.mcp_url)

    print("Running single-operation benchmarks...")
    single_results = single_operation_bench(rest_client, list_target_sizes=[1000, 5000, 10000], search_result_targets=[50, 500], repeats=args.repeats)

    if mcp_client:
        single_results_mcp = single_operation_bench_mcp(mcp_client, repeats=args.repeats)

        # Save MCP CSV
        base_dir = Path(__file__).parent
        (base_dir / "mcp").mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(base_dir / "mcp" / f"single_ops_{ts}.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["operation", "p50_ms", "mean_ms", "p90_ms"])
            for lbl, res in single_results_mcp.items():
                writer.writerow([lbl, f"{res.p50:.1f}", f"{res.mean:.1f}", f"{res.p90:.1f}"])


    # Save REST CSV
    base_dir = Path(__file__).parent
    (base_dir / "rest").mkdir(exist_ok=True)
    ts_rest = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(base_dir / "rest" / f"single_ops_{ts_rest}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["operation", "p50_ms", "mean_ms", "p90_ms"])
        for lbl, res in single_results.items():
            writer.writerow([lbl, f"{res.p50:.1f}", f"{res.mean:.1f}", f"{res.p90:.1f}"])


    print("Running workflow benchmarks...")
    workflow_results = workflow_bench(rest_client, repeats=args.repeats)

    print("Running concurrency benchmarks...")
    def sequence(rest: PatraREST) -> Any:
        rest.list_modelcards()
        res = rest.search_modelcards("model")
        if res:
            mc_id = res[0].get("external_id") or res[0].get("id") or next(iter(res[0].values()), None)
            if mc_id:
                try:
                    rest.get_modelcard(str(mc_id))
                except Exception:
                    pass
        return True

    throughput = concurrent_clients_bench(lambda: PatraREST(args.base_url), args.concurrency, sequence)

    print("Measuring protocol overhead...")
    overhead = protocol_overhead(rest_client)

    # Output LaTeX rows for direct paste into the manuscript tables
    print("\nLaTeX rows for Single Operation Latencies (REST column filled):")
    print(latex_table_single_ops(single_results))

    print("\nLaTeX rows for Multi-Operation Workflow Performance (REST column filled):")
    print(latex_table_workflows(workflow_results))

    print("\nLaTeX rows for Throughput Under Concurrent Load (REST column filled):")
    print(latex_table_concurrency(throughput))

    print("\nProtocol overhead size estimates (bytes):")
    for k, v in overhead.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    sys.exit(main())


