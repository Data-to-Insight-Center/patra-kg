import argparse
import csv
import statistics
import time
from typing import List, Callable

import requests


def get_modelcard(base: str, mc_id: str):
    resp = requests.get(f"{base}/modelcard/{mc_id}")
    resp.raise_for_status()
    return resp.json()


def search_modelcards(base: str, query: str):
    resp = requests.get(f"{base}/modelcards/search", params={"q": query})
    resp.raise_for_status()
    return resp.json()


def list_modelcards(base: str):
    resp = requests.get(f"{base}/modelcards")
    resp.raise_for_status()
    return resp.json()


def measure_latency(fn: Callable[[], None], repeats: int) -> List[float]:
    samples: List[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    return samples


def microbench(base_url: str, mc_id: str, repeats: int, output_dir: str):
    print(f"REST microbenchmark against {base_url}  repeats={repeats}")

    import os
    os.makedirs(output_dir, exist_ok=True)

    # list_modelcards
    print("Benchmarking list_modelcards …")
    list_samples = measure_latency(lambda: list_modelcards(base_url), repeats)
    list_csv = f"{output_dir}/rest_list_modelcards_latency.csv"
    with open(list_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample", "latency_ms"])
        for i, v in enumerate(list_samples, 1):
            writer.writerow([i, round(v, 3)])
    print(f"  p50={statistics.median(list_samples):.3f} ms  saved → {list_csv}\n")

    # get_modelcard
    print("Benchmarking get_modelcard …")
    get_samples = measure_latency(lambda: get_modelcard(base_url, mc_id), repeats)
    get_csv = f"{output_dir}/rest_get_modelcard_latency.csv"
    with open(get_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample", "latency_ms"])
        for i, v in enumerate(get_samples, 1):
            writer.writerow([i, round(v, 3)])
    print(f"  p50={statistics.median(get_samples):.3f} ms  saved → {get_csv}\n")

    # search_modelcards
    print("Benchmarking search_modelcards …")
    search_samples = measure_latency(lambda: search_modelcards(base_url, "googlenet"), repeats)
    search_csv = f"{output_dir}/rest_search_modelcards_latency.csv"
    with open(search_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample", "latency_ms"])
        for i, v in enumerate(search_samples, 1):
            writer.writerow([i, round(v, 3)])
    print(f"  p50={statistics.median(search_samples):.3f} ms  saved → {search_csv}\n")


def main():
    parser = argparse.ArgumentParser(description="Simple REST microbenchmark")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000", help="REST base URL")
    parser.add_argument("--mc-id", default="neelk_googlenet-0024_1.0", help="Model card id for get benchmark")
    parser.add_argument("--repeats", type=int, default=10, help="Number of repetitions")
    parser.add_argument("--output-dir", default="benchmarking/results", help="Dir for CSV output")

    args = parser.parse_args()

    microbench(args.base_url.rstrip("/"), args.mc_id, args.repeats, args.output_dir)


if __name__ == "__main__":
    main()