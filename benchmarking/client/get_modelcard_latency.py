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
from typing import List, Optional

import requests


DEFAULT_BASE_URL = os.environ.get("PATRA_BASE_URL", "http://localhost:5002").rstrip("/")


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


def ingest_sample_modelcard(base_url: str) -> Optional[str]:
    payload = {
        "name": "resnet152",
        "version": "1.0",
        "short_description": "Image classification using ResNet-152.",
        "full_description": "ResNet-152 deep CNN with residual connections.",
        "keywords": "image classification, ResNet-152",
        "author": "benchmark",
        "input_type": "images",
        "category": "classification",
        "input_data": "https://www.image-net.org/",
        "output_data": "https://huggingface.co/patra-iu/benchmark-resnet152-1.0",
        "foundational_model": "None",
        "citation": "He et al., Deep Residual Learning for Image Recognition",
        "ai_model": {
            "name": "resnet152",
            "version": "1.0",
            "description": "CNN with residual blocks",
            "owner": "benchmark",
            "location": "https://huggingface.co/patra-iu/benchmark-resnet152-1.0/blob/main/model.pth",
            "license": "BSD-3-Clause",
            "framework": "pytorch",
            "model_type": "cnn",
            "test_accuracy": 0.7,
            "inference_labels": [],
            "metrics": {"Precision": 0.7},
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": [],
    }

    try:
        resp = requests.post(f"{base_url}/modelcard", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("model_card_id")
    except Exception as e:
        print(f"Failed to ingest sample model card: {e}", file=sys.stderr)
        return None


def warmup(session: requests.Session, url: str, count: int) -> None:
    for _ in range(max(0, count)):
        try:
            r = session.get(url, timeout=10)
            r.raise_for_status()
        except Exception:
            pass


def run_sequential(session: requests.Session, url: str, repeats: int) -> List[float]:
    samples: List[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        resp = session.get(url, timeout=30)
        t1 = time.perf_counter()
        resp.raise_for_status()
        samples.append((t1 - t0) * 1000.0)
    return samples


def run_concurrent(session: requests.Session, url: str, repeats: int, workers: int) -> List[float]:
    durations: List[float] = []

    def _one_call() -> float:
        t0 = time.perf_counter()
        resp = session.get(url, timeout=30)
        t1 = time.perf_counter()
        resp.raise_for_status()
        return (t1 - t0) * 1000.0

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [executor.submit(_one_call) for _ in range(repeats)]
        for fut in as_completed(futures):
            durations.append(fut.result())
    return durations


def save_csv(csv_path: Path, mc_id: str, repeats: int, stats: LatencyStats, raw_samples: Optional[List[float]] = None) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mc_id", "repeats", "p50_ms", "mean_ms", "p90_ms"])
        w.writerow([mc_id, repeats, stats.p50_ms, stats.mean_ms, stats.p90_ms])

    if raw_samples is not None:
        raw_path = csv_path.parent / (csv_path.stem + "_raw" + csv_path.suffix)
        with raw_path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["latency_ms"])
            for v in raw_samples:
                w.writerow([v])


def main() -> int:
    parser = argparse.ArgumentParser(description="Latency microbenchmark for GET /modelcard/{mc_id}")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of REST API (default: %(default)s)")
    parser.add_argument("--mc-id", help="Model card ID to fetch. If omitted and --ingest-sample is set, a sample will be created.")
    parser.add_argument("--repeats", type=int, default=50, help="Number of measured requests (default: %(default)s)")
    parser.add_argument("--warmup", type=int, default=5, help="Warmup requests before timing (default: %(default)s)")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent workers (1 for sequential) (default: %(default)s)")
    parser.add_argument("--out-csv", default=str(Path("benchmarking/results/get_modelcard_latency.csv")), help="Output CSV path (default: %(default)s)")
    parser.add_argument("--ingest-sample", action="store_true", help="Ingest a sample model card if mc_id is not provided")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    mc_id = args.mc_id
    if not mc_id:
        if args.ingest_sample:
            mc_id = ingest_sample_modelcard(base_url)
            if not mc_id:
                print("Could not determine mc_id. Aborting.", file=sys.stderr)
                return 1
        else:
            print("--mc-id is required (or pass --ingest-sample)", file=sys.stderr)
            return 1

    url = f"{base_url}/modelcard/{mc_id}"
    session = requests.Session()
    session.headers.update({"Connection": "keep-alive"})

    warmup(session, url, args.warmup)

    if args.workers <= 1:
        samples = run_sequential(session, url, args.repeats)
    else:
        samples = run_concurrent(session, url, args.repeats, args.workers)

    stats = compute_stats(samples)
    print(json.dumps({
        "mc_id": mc_id,
        "repeats": args.repeats,
        "workers": args.workers,
        "p50_ms": stats.p50_ms,
        "mean_ms": stats.mean_ms,
        "p90_ms": stats.p90_ms,
    }, indent=2))

    save_csv(Path(args.out_csv), mc_id, args.repeats, stats, raw_samples=samples)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


