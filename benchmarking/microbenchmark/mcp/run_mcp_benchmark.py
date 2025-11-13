#!/usr/bin/env python3
"""
Simple MCP timing benchmark - equivalent to curl timing breakdown.

Measures individual request timings broken down into phases:
- SSE connection time
- MCP initialization/handshake time
- Resource read time
- Total time
"""

import asyncio
import time
import csv
from datetime import datetime
from mcp import ClientSession
from mcp.client.sse import sse_client


# Configuration
MODELCARD_ID = "megadetector-mc-9aaede5b"
NUM_REQUESTS = 100

# Benchmark configurations
BENCHMARKS = [
    {
        'name': 'Native MCP',
        'server_url': 'http://149.165.175.102:8050',
        'csv_file': 'native_mcp_timing_results.csv'
    },
    {
        'name': 'MCP',
        'server_url': 'http://149.165.175.102:8051',
        'csv_file': 'mcp_timing_results.csv'
    }
]


async def single_timed_request(request_id: int, sse_url: str) -> dict:
    """Execute a single MCP request with timing breakdown."""
    timings = {
        'request_id': request_id,
        'connection_ms': 0,
        'handshake_ms': 0,
        'resource_read_ms': 0,
        'total_time_ms': 0,
        'status': 'failed'
    }

    start_total = time.perf_counter()

    try:
        # Phase 1: SSE Connection
        start_connection = time.perf_counter()
        transport = sse_client(url=sse_url)
        read_stream, write_stream = await transport.__aenter__()
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()
        end_connection = time.perf_counter()
        timings['connection_ms'] = (end_connection - start_connection) * 1000

        # Phase 2: MCP Handshake
        start_handshake = time.perf_counter()
        await session.initialize()
        end_handshake = time.perf_counter()
        timings['handshake_ms'] = (end_handshake - start_handshake) * 1000

        # Phase 3: Resource Read
        start_read = time.perf_counter()
        uri = f"modelcard://{MODELCARD_ID}"
        result = await session.read_resource(uri)
        end_read = time.perf_counter()
        timings['resource_read_ms'] = (end_read - start_read) * 1000

        # Success
        timings['status'] = 'success'

        # Cleanup
        try:
            await session.__aexit__(None, None, None)
            await transport.__aexit__(None, None, None)
        except Exception:
            pass

    except Exception as e:
        timings['status'] = f'error: {str(e)[:50]}'

    end_total = time.perf_counter()
    timings['total_time_ms'] = (end_total - start_total) * 1000

    return timings


async def run_benchmark(benchmark_name: str, server_url: str, csv_file: str):
    """Run the complete benchmark for a given configuration."""
    sse_url = f"{server_url}/sse"

    print(f"\n{'=' * 70}")
    print(f"Running {benchmark_name} benchmark")
    print(f"{'=' * 70}")
    print(f"Server URL: {sse_url}")
    print(f"Requests: {NUM_REQUESTS}")
    print(f"Results will be saved to: {csv_file}")
    print("")

    # Initialize CSV file with header
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'request_id',
            'connection_ms',
            'handshake_ms',
            'resource_read_ms',
            'total_time_ms',
            'status'
        ])

    # Warm-up phase
    print("Running warm-up phase (10 requests)...")
    for i in range(1, 11):
        print(f"Warm-up request {i}/10... ", end='', flush=True)
        await single_timed_request(0, sse_url)  # Request ID 0 for warm-up
        print("Done")
    print("Warm-up complete! Starting measurements...")
    print("")

    # Run requests sequentially
    results = []
    for i in range(1, NUM_REQUESTS + 1):
        print(f"Request {i}/{NUM_REQUESTS}... ", end='', flush=True)

        timing = await single_timed_request(i, sse_url)
        results.append(timing)

        # Write to CSV
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timing['request_id'],
                f"{timing['connection_ms']:.3f}",
                f"{timing['handshake_ms']:.3f}",
                f"{timing['resource_read_ms']:.3f}",
                f"{timing['total_time_ms']:.3f}",
                timing['status']
            ])

        print("Done")

    print("")
    print(f"{benchmark_name} benchmark complete!")
    print(f"Results saved to: {csv_file}")

    # Calculate and print summary statistics
    successful = [r for r in results if r['status'] == 'success']
    if successful:
        avg_connection = sum(r['connection_ms'] for r in successful) / len(successful)
        avg_handshake = sum(r['handshake_ms'] for r in successful) / len(successful)
        avg_read = sum(r['resource_read_ms'] for r in successful) / len(successful)
        avg_total = sum(r['total_time_ms'] for r in successful) / len(successful)

        print(f"\nSummary Statistics ({len(successful)}/{NUM_REQUESTS} successful):")
        print(f"  Avg SSE Connection:    {avg_connection:.3f} ms")
        print(f"  Avg MCP Handshake:     {avg_handshake:.3f} ms")
        print(f"  Avg Resource Read:     {avg_read:.3f} ms")
        print(f"  Avg Total Time:        {avg_total:.3f} ms")


async def main():
    """Run all benchmarks sequentially."""
    print("=" * 70)
    print("MCP Timing Benchmark Suite")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"ModelCard ID: {MODELCARD_ID}")
    print("=" * 70)

    for benchmark in BENCHMARKS:
        await run_benchmark(
            benchmark_name=benchmark['name'],
            server_url=benchmark['server_url'],
            csv_file=benchmark['csv_file']
        )

    print("\n" + "=" * 70)
    print("All benchmarks complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
