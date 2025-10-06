import argparse
import asyncio
import csv
import os
import statistics
import time
from typing import List

from fastmcp import Client


async def measure_latency(client: Client, method: str, params: dict, repeats: int) -> List[float]:
    """Run an MCP tool multiple times and return a list of per-call latencies (ms)."""
    samples: List[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        result = await client.call_tool(method, params)
        samples.append((time.perf_counter() - t0) * 1000.0)
    return samples


async def run_bench(endpoint: str, mc_id: str, repeats: int, output_dir: str) -> None:
    client = Client(endpoint)

    async with client:
        tools = await client.list_tools()
        print("Available tools:", [t.name for t in tools])

        os.makedirs(output_dir, exist_ok=True)

        # 1. Benchmark list_modelcards (no parameters)
        print("Benchmarking list_modelcards …")
        list_samples = await measure_latency(client, "list_modelcards", {}, repeats)
        list_csv = os.path.join(output_dir, "simple_list_modelcards_latency.csv")
        with open(list_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["sample", "latency_ms"])
            for i, v in enumerate(list_samples, 1):
                writer.writerow([i, round(v, 3)])
        print(f"  p50={statistics.median(list_samples):.3f} ms  saved → {list_csv} \n")

        # 2. Benchmark get_modelcard
        print("Benchmarking get_modelcard …")
        get_samples = await measure_latency(client, "get_modelcard", {"mc_id": mc_id}, repeats)
        get_csv = os.path.join(output_dir, "simple_get_modelcard_latency.csv")
        with open(get_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["sample", "latency_ms"])
            for i, v in enumerate(get_samples, 1):
                writer.writerow([i, round(v, 3)])
        print(f"  p50={statistics.median(get_samples):.3f} ms  saved → {get_csv} \n")

        # 3. Benchmark search_modelcards
        print("Benchmarking search_modelcards …")
        search_samples = await measure_latency(client, "search_modelcards", {"q": "googlenet"}, repeats)
        search_csv = os.path.join(output_dir, "simple_search_modelcards_latency.csv")
        with open(search_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["sample", "latency_ms"])
            for i, v in enumerate(search_samples, 1):
                writer.writerow([i, round(v, 3)])
        print(f"  p50={statistics.median(search_samples):.3f} ms  saved → {search_csv} \n")


def main() -> None:
    # FastMCP HTTP servers expose their API under the "/mcp" sub-path.
    # Point the client at that full path so it hits the correct route.
    default_endpoint = "http://localhost:5001/mcp"

    parser = argparse.ArgumentParser(description="Simple MCP microbenchmark")
    parser.add_argument(
        "--endpoint",
        default=default_endpoint,
        help="MCP transport endpoint (default: %(default)s)",
    )
    parser.add_argument("--mc-id", default="neelk_googlenet-0024_1.0", help="Model card ID to benchmark for get_modelcard")
    parser.add_argument("--repeats", type=int, default=1, help="Number of repetitions per benchmark")
    parser.add_argument("--output-dir", default="benchmarking/results", help="Directory to write CSV latency files")

    args = parser.parse_args()

    asyncio.run(run_bench(args.endpoint, args.mc_id, args.repeats, args.output_dir))


if __name__ == "__main__":
    main()
