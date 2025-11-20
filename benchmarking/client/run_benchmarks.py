#!/usr/bin/env python3
"""
Unified benchmark script that runs all three implementations sequentially.
Generates three CSV files: rest_timing_results.csv, native_mcp_timing_results.csv, layered_mcp_timing_results.csv
"""

import os
import sys
import asyncio
import time
import csv
import json
import subprocess
from datetime import datetime
from mcp import ClientSession
from mcp.client.sse import sse_client
from utils import (
    run_curl_request,
    extract_mcp_timing_fields,
    create_timing_dict
)

# Configuration from environment variables
CLIENT_REGION = os.getenv("CLIENT_REGION", "same_region")
REST_SERVER_URL = os.getenv("REST_SERVER_URL", "http://rest-server:5002")
NATIVE_MCP_URL = os.getenv("NATIVE_MCP_URL", "http://mcp-server:8050")
LAYERED_MCP_URL = os.getenv("LAYERED_MCP_URL", "http://layered-mcp-server:8051")
MODEL_CARD_ID = os.getenv("MODEL_CARD_ID", "megadetector-mc-9aaede5b")
SOURCE_NODE_ID = os.getenv("SOURCE_NODE_ID", "4:995d2e90-888a-4c7c-a7bc-e9188e945381:37")
TARGET_NODE_ID = os.getenv("TARGET_NODE_ID", "4:995d2e90-888a-4c7c-a7bc-e9188e945381:38")
NUM_REQUESTS = int(os.getenv("NUM_REQUESTS", "100"))
WARMUP_REQUESTS = int(os.getenv("WARMUP_REQUESTS", "10"))

# Results directory
RESULTS_DIR = f"/app/results/{CLIENT_REGION}"
os.makedirs(RESULTS_DIR, exist_ok=True)


# ============================================================================
# REST API Benchmarks
# ============================================================================

async def run_rest_modelcard_benchmark(csv_writer):
    """Run REST API model card retrieval benchmark using curl for accurate timing."""
    print(f"\n{'=' * 70}")
    print("Running REST API Model Card Retrieval Benchmark")
    print(f"{'=' * 70}")
    
    url = f"{REST_SERVER_URL}/modelcard/{MODEL_CARD_ID}"
    
    # Warm-up phase
    print(f"Running warm-up phase ({WARMUP_REQUESTS} requests)...")
    for i in range(WARMUP_REQUESTS):
        try:
            subprocess.run(
                ["curl", "-o", "/dev/null", "-s", url],
                check=False,
                capture_output=True
            )
        except Exception:
            pass
    
    print("Warm-up complete! Starting measurements...")
    
    # Run requests
    for i in range(1, NUM_REQUESTS + 1):
        print(f"Request {i}/{NUM_REQUESTS}... ", end='', flush=True)
        
        try:
            # Use curl utility to get detailed timing and headers
            result = run_curl_request(url, method="GET")
            
            csv_writer.writerow([
                i,
                result['dns_lookup_ms'],
                result['tcp_connect_ms'],
                result['tls_handshake_ms'],
                result['time_pretransfer_ms'],
                result['time_to_first_byte_ms'],
                result['total_time_ms'],
                result['database_ms'],
                "modelcard"
            ])
            print("Done")
        except Exception as e:
            print(f"Error: {str(e)[:50]}")
            csv_writer.writerow([
                i, 0, 0, 0, 0, 0, 0, 0, "modelcard"
            ])


async def run_rest_edge_benchmark(csv_writer):
    """Run REST API edge creation benchmark using curl for accurate timing."""
    print(f"\n{'=' * 70}")
    print("Running REST API Edge Creation Benchmark")
    print(f"{'=' * 70}")
    
    url = f"{REST_SERVER_URL}/edge"
    json_data = json.dumps({
        "source_node_id": SOURCE_NODE_ID,
        "target_node_id": TARGET_NODE_ID
    })
    
    # Warm-up phase
    print(f"Running warm-up phase ({WARMUP_REQUESTS} requests)...")
    for i in range(WARMUP_REQUESTS):
        try:
            # Delete edge first
            subprocess.run(
                ["curl", "-X", "DELETE", "-o", "/dev/null", "-s", "-H", "Content-Type: application/json",
                 "-d", json_data, url],
                check=False,
                capture_output=True
            )
            # Create edge
            subprocess.run(
                ["curl", "-X", "POST", "-o", "/dev/null", "-s", "-H", "Content-Type: application/json",
                 "-d", json_data, url],
                check=False,
                capture_output=True
            )
        except Exception:
            pass
    
    print("Warm-up complete! Starting measurements...")
    
    # Run requests
    for i in range(1, NUM_REQUESTS + 1):
        print(f"Request {i}/{NUM_REQUESTS}... ", end='', flush=True)
        
        # Delete edge first (not timed)
        try:
            subprocess.run(
                ["curl", "-X", "DELETE", "-o", "/dev/null", "-s", "-H", "Content-Type: application/json",
                 "-d", json_data, url],
                check=False,
                capture_output=True
            )
        except Exception:
            pass
        
        try:
            # Use curl utility to get detailed timing and headers for POST
            result = run_curl_request(url, method="POST", json_data=json_data)
            
            csv_writer.writerow([
                i,
                result['dns_lookup_ms'],
                result['tcp_connect_ms'],
                result['tls_handshake_ms'],
                result['time_pretransfer_ms'],
                result['time_to_first_byte_ms'],
                result['total_time_ms'],
                result['database_ms'],
                "edge"
            ])
            print("Done")
        except Exception as e:
            print(f"Error: {str(e)[:50]}")
            csv_writer.writerow([
                i, 0, 0, 0, 0, 0, 0, 0, "edge"
            ])


# ============================================================================
# Native MCP Benchmarks
# ============================================================================

async def run_native_mcp_modelcard_benchmark(csv_writer):
    """Run Native MCP model card retrieval benchmark."""
    print(f"\n{'=' * 70}")
    print("Running Native MCP Model Card Retrieval Benchmark")
    print(f"{'=' * 70}")
    
    sse_url = f"{NATIVE_MCP_URL}/sse"
    
    # Warm-up phase
    print(f"Running warm-up phase ({WARMUP_REQUESTS} requests)...")
    for i in range(WARMUP_REQUESTS):
        try:
            await single_mcp_resource_request(0, sse_url, MODEL_CARD_ID)
        except Exception:
            pass
    
    print("Warm-up complete! Starting measurements...")
    
    # Run requests
    for i in range(1, NUM_REQUESTS + 1):
        print(f"Request {i}/{NUM_REQUESTS}... ", end='', flush=True)
        timings = await single_mcp_resource_request(i, sse_url, MODEL_CARD_ID)
        csv_writer.writerow([
            timings['request_id'],
            timings['connection_ms'],
            timings['handshake_ms'],
            timings['resource_read_ms'],
            0,  # tool_call_ms
            timings['total_time_ms'],
            timings['database_ms'],
            "modelcard"
        ])
        print("Done")


async def run_native_mcp_edge_benchmark(csv_writer):
    """Run Native MCP edge creation benchmark."""
    print(f"\n{'=' * 70}")
    print("Running Native MCP Edge Creation Benchmark")
    print(f"{'=' * 70}")
    
    sse_url = f"{NATIVE_MCP_URL}/sse"
    
    # Warm-up phase
    print(f"Running warm-up phase ({WARMUP_REQUESTS} requests)...")
    for i in range(WARMUP_REQUESTS):
        try:
            await single_mcp_tool_request(0, sse_url, SOURCE_NODE_ID, TARGET_NODE_ID)
        except Exception:
            pass
    
    print("Warm-up complete! Starting measurements...")
    
    # Run requests
    for i in range(1, NUM_REQUESTS + 1):
        print(f"Request {i}/{NUM_REQUESTS}... ", end='', flush=True)
        timings = await single_mcp_tool_request(i, sse_url, SOURCE_NODE_ID, TARGET_NODE_ID)
        csv_writer.writerow([
            timings['request_id'],
            timings['connection_ms'],
            timings['handshake_ms'],
            0,  # resource_read_ms
            timings['tool_call_ms'],
            timings['total_time_ms'],
            timings['database_ms'],
            "edge"
        ])
        print("Done")


async def single_mcp_resource_request(request_id: int, sse_url: str, mc_id: str) -> dict:
    """Execute a single MCP resource read request with timing breakdown."""
    timings = create_timing_dict(request_id)
    
    start_total = time.perf_counter()
    
    try:
        # Phase 1: SSE Connection
        start_connection = time.perf_counter()
        async with sse_client(url=sse_url) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            async with session:
                end_connection = time.perf_counter()
                timings['connection_ms'] = (end_connection - start_connection) * 1000
                
                # Phase 2: MCP Handshake
                start_handshake = time.perf_counter()
                await session.initialize()
                end_handshake = time.perf_counter()
                timings['handshake_ms'] = (end_handshake - start_handshake) * 1000
                
                # Phase 3: Resource Read
                start_read = time.perf_counter()
                uri = f"modelcard://{mc_id}"
                result = await session.read_resource(uri)
                end_read = time.perf_counter()
                timings['resource_read_ms'] = (end_read - start_read) * 1000
                
                # Extract database_ms from result
                timing_fields = extract_mcp_timing_fields(result, is_layered=False)
                timings['database_ms'] = timing_fields['database_ms']
                
                timings['status'] = 'success'
    
    except Exception as e:
        timings['status'] = f'error: {str(e)[:50]}'
    
    end_total = time.perf_counter()
    timings['total_time_ms'] = (end_total - start_total) * 1000
    
    return timings


async def single_mcp_tool_request(request_id: int, sse_url: str, source_node_id: str, target_node_id: str) -> dict:
    """Execute a single MCP tool call request with timing breakdown."""
    timings = create_timing_dict(request_id)
    
    start_total = time.perf_counter()
    
    try:
        # Phase 1: SSE Connection
        start_connection = time.perf_counter()
        async with sse_client(url=sse_url) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            async with session:
                end_connection = time.perf_counter()
                timings['connection_ms'] = (end_connection - start_connection) * 1000
                
                # Phase 2: MCP Handshake
                start_handshake = time.perf_counter()
                await session.initialize()
                end_handshake = time.perf_counter()
                timings['handshake_ms'] = (end_handshake - start_handshake) * 1000
                
                # Delete edge first (not timed)
                try:
                    await session.call_tool("delete_edge", {
                        "source_node_id": source_node_id,
                        "target_node_id": target_node_id
                    })
                except Exception:
                    pass
                
                # Phase 3: Tool Call
                start_tool = time.perf_counter()
                result = await session.call_tool("create_edge", {
                    "source_node_id": source_node_id,
                    "target_node_id": target_node_id
                })
                end_tool = time.perf_counter()
                timings['tool_call_ms'] = (end_tool - start_tool) * 1000
                
                # Extract database_ms from result
                timing_fields = extract_mcp_timing_fields(result, is_layered=False)
                timings['database_ms'] = timing_fields['database_ms']
                
                timings['status'] = 'success'
    
    except Exception as e:
        timings['status'] = f'error: {str(e)[:50]}'
    
    end_total = time.perf_counter()
    timings['total_time_ms'] = (end_total - start_total) * 1000
    
    return timings


# ============================================================================
# Layered MCP Benchmarks
# ============================================================================

async def run_layered_mcp_modelcard_benchmark(csv_writer):
    """Run Layered MCP model card retrieval benchmark."""
    print(f"\n{'=' * 70}")
    print("Running Layered MCP Model Card Retrieval Benchmark")
    print(f"{'=' * 70}")
    
    sse_url = f"{LAYERED_MCP_URL}/sse"
    
    # Warm-up phase
    print(f"Running warm-up phase ({WARMUP_REQUESTS} requests)...")
    for i in range(WARMUP_REQUESTS):
        try:
            await single_layered_mcp_resource_request(0, sse_url, MODEL_CARD_ID)
        except Exception:
            pass
    
    print("Warm-up complete! Starting measurements...")
    
    # Run requests
    for i in range(1, NUM_REQUESTS + 1):
        print(f"Request {i}/{NUM_REQUESTS}... ", end='', flush=True)
        timings = await single_layered_mcp_resource_request(i, sse_url, MODEL_CARD_ID)
        csv_writer.writerow([
            timings['request_id'],
            timings['connection_ms'],
            timings['handshake_ms'],
            timings['resource_read_ms'],
            0,  # tool_call_ms
            timings['total_time_ms'],
            timings['database_ms'],
            timings['rest_ms'],
            "modelcard"
        ])
        print("Done")


async def run_layered_mcp_edge_benchmark(csv_writer):
    """Run Layered MCP edge creation benchmark."""
    print(f"\n{'=' * 70}")
    print("Running Layered MCP Edge Creation Benchmark")
    print(f"{'=' * 70}")
    
    sse_url = f"{LAYERED_MCP_URL}/sse"
    
    # Warm-up phase
    print(f"Running warm-up phase ({WARMUP_REQUESTS} requests)...")
    for i in range(WARMUP_REQUESTS):
        try:
            await single_layered_mcp_tool_request(0, sse_url, SOURCE_NODE_ID, TARGET_NODE_ID)
        except Exception:
            pass
    
    print("Warm-up complete! Starting measurements...")
    
    # Run requests
    for i in range(1, NUM_REQUESTS + 1):
        print(f"Request {i}/{NUM_REQUESTS}... ", end='', flush=True)
        timings = await single_layered_mcp_tool_request(i, sse_url, SOURCE_NODE_ID, TARGET_NODE_ID)
        csv_writer.writerow([
            timings['request_id'],
            timings['connection_ms'],
            timings['handshake_ms'],
            0,  # resource_read_ms
            timings['tool_call_ms'],
            timings['total_time_ms'],
            timings['database_ms'],
            timings['rest_ms'],
            "edge"
        ])
        print("Done")


async def single_layered_mcp_resource_request(request_id: int, sse_url: str, mc_id: str) -> dict:
    """Execute a single Layered MCP resource read request with timing breakdown."""
    timings = create_timing_dict(request_id)
    
    start_total = time.perf_counter()
    
    try:
        # Phase 1: SSE Connection
        start_connection = time.perf_counter()
        async with sse_client(url=sse_url) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            async with session:
                end_connection = time.perf_counter()
                timings['connection_ms'] = (end_connection - start_connection) * 1000
                
                # Phase 2: MCP Handshake
                start_handshake = time.perf_counter()
                await session.initialize()
                end_handshake = time.perf_counter()
                timings['handshake_ms'] = (end_handshake - start_handshake) * 1000
                
                # Phase 3: Resource Read
                start_read = time.perf_counter()
                uri = f"modelcard://{mc_id}"
                result = await session.read_resource(uri)
                end_read = time.perf_counter()
                timings['resource_read_ms'] = (end_read - start_read) * 1000
                
                # Extract database_ms and rest_ms from result
                timing_fields = extract_mcp_timing_fields(result, is_layered=True)
                timings['database_ms'] = timing_fields['database_ms']
                timings['rest_ms'] = timing_fields['rest_ms']
                
                timings['status'] = 'success'
    
    except Exception as e:
        timings['status'] = f'error: {str(e)[:50]}'
    
    end_total = time.perf_counter()
    timings['total_time_ms'] = (end_total - start_total) * 1000
    
    return timings


async def single_layered_mcp_tool_request(request_id: int, sse_url: str, source_node_id: str, target_node_id: str) -> dict:
    """Execute a single Layered MCP tool call request with timing breakdown."""
    timings = create_timing_dict(request_id)
    
    start_total = time.perf_counter()
    
    try:
        # Phase 1: SSE Connection
        start_connection = time.perf_counter()
        async with sse_client(url=sse_url) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            async with session:
                end_connection = time.perf_counter()
                timings['connection_ms'] = (end_connection - start_connection) * 1000
                
                # Phase 2: MCP Handshake
                start_handshake = time.perf_counter()
                await session.initialize()
                end_handshake = time.perf_counter()
                timings['handshake_ms'] = (end_handshake - start_handshake) * 1000
                
                # Delete edge first (not timed)
                try:
                    await session.call_tool("delete_edge", {
                        "source_node_id": source_node_id,
                        "target_node_id": target_node_id
                    })
                except Exception:
                    pass
                
                # Phase 3: Tool Call
                start_tool = time.perf_counter()
                result = await session.call_tool("create_edge", {
                    "source_node_id": source_node_id,
                    "target_node_id": target_node_id
                })
                end_tool = time.perf_counter()
                timings['tool_call_ms'] = (end_tool - start_tool) * 1000
                
                # Extract database_ms and rest_ms from result
                timing_fields = extract_mcp_timing_fields(result, is_layered=True)
                timings['database_ms'] = timing_fields['database_ms']
                timings['rest_ms'] = timing_fields['rest_ms']
                
                timings['status'] = 'success'
    
    except Exception as e:
        timings['status'] = f'error: {str(e)[:50]}'
    
    end_total = time.perf_counter()
    timings['total_time_ms'] = (end_total - start_total) * 1000
    
    return timings


# ============================================================================
# Main Execution
# ============================================================================

async def main():
    """Main function to run all benchmarks sequentially."""
    print("=" * 70)
    print("Latency Micro-Benchmark Suite")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Client Region: {CLIENT_REGION}")
    print(f"Number of Requests: {NUM_REQUESTS}")
    print("=" * 70)
    
    # REST API Benchmarks
    rest_csv_path = os.path.join(RESULTS_DIR, "rest_timing_results.csv")
    with open(rest_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'request_id', 'dns_lookup_ms', 'tcp_connect_ms', 'tls_handshake_ms',
            'time_pretransfer_ms', 'time_to_first_byte_ms', 'total_time_ms',
            'database_ms', 'operation_type'
        ])
        await run_rest_modelcard_benchmark(writer)
        # await run_rest_edge_benchmark(writer)
    print(f"\nREST results saved to: {rest_csv_path}")
    
    # # Native MCP Benchmarks
    # native_mcp_csv_path = os.path.join(RESULTS_DIR, "native_mcp_timing_results.csv")
    # with open(native_mcp_csv_path, 'w', newline='') as f:
    #     writer = csv.writer(f)
    #     writer.writerow([
    #         'request_id', 'connection_ms', 'handshake_ms', 'resource_read_ms',
    #         'tool_call_ms', 'total_time_ms', 'database_ms', 'operation_type'
    #     ])
    #     await run_native_mcp_modelcard_benchmark(writer)
    #     await run_native_mcp_edge_benchmark(writer)
    # print(f"\nNative MCP results saved to: {native_mcp_csv_path}")
    
    # # Layered MCP Benchmarks
    # layered_mcp_csv_path = os.path.join(RESULTS_DIR, "layered_mcp_timing_results.csv")
    # with open(layered_mcp_csv_path, 'w', newline='') as f:
    #     writer = csv.writer(f)
    #     writer.writerow([
    #         'request_id', 'connection_ms', 'handshake_ms', 'resource_read_ms',
    #         'tool_call_ms', 'total_time_ms', 'database_ms', 'rest_ms', 'operation_type'
    #     ])
    #     await run_layered_mcp_modelcard_benchmark(writer)
    #     await run_layered_mcp_edge_benchmark(writer)
    # print(f"\nLayered MCP results saved to: {layered_mcp_csv_path}")
    
    # print("\n" + "=" * 70)
    # print("All benchmarks complete!")
    # print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

