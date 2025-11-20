#!/usr/bin/env python3
"""
Utility functions for benchmark script.
"""

import json
import subprocess
import time
from typing import Dict, Any, Optional


def extract_database_ms_from_headers(header_file: str) -> float:
    """Extract database latency from curl response headers."""
    try:
        with open(header_file, "r") as f:
            for line in f:
                if "X-Database-Latency-MS" in line:
                    return float(line.split(":", 1)[1].strip())
    except Exception:
        pass
    return 0.0


def extract_database_ms_from_json(json_file: str) -> float:
    """Extract database latency from JSON response file."""
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
            return float(data.get("database_ms", 0))
    except Exception:
        pass
    return 0.0


def parse_curl_timing_output(timing_output: str) -> Dict[str, float]:
    """Parse curl timing output and return timing components in milliseconds."""
    timing_parts = timing_output.strip().split(',')
    
    if len(timing_parts) == 6:
        dns_lookup_ms = float(timing_parts[0]) * 1000
        tcp_connect_ms = float(timing_parts[1]) * 1000
        tls_handshake_ms = (float(timing_parts[2]) - float(timing_parts[1])) * 1000 if float(timing_parts[2]) > 0 else 0
        time_pretransfer_ms = float(timing_parts[3]) * 1000
        time_to_first_byte_ms = float(timing_parts[4]) * 1000
        total_time_ms = float(timing_parts[5]) * 1000
        
        return {
            'dns_lookup_ms': dns_lookup_ms,
            'tcp_connect_ms': tcp_connect_ms,
            'tls_handshake_ms': tls_handshake_ms,
            'time_pretransfer_ms': time_pretransfer_ms,
            'time_to_first_byte_ms': time_to_first_byte_ms,
            'total_time_ms': total_time_ms
        }
    else:
        return {
            'dns_lookup_ms': 0.0,
            'tcp_connect_ms': 0.0,
            'tls_handshake_ms': 0.0,
            'time_pretransfer_ms': 0.0,
            'time_to_first_byte_ms': 0.0,
            'total_time_ms': 0.0
        }


def run_curl_request(url: str, method: str = "GET", json_data: Optional[str] = None, 
                     headers: Optional[list] = None) -> Dict[str, Any]:
    """
    Run a curl request and return timing information and response details.
    
    Returns:
        Dictionary with timing info, database_ms, and response data
    """
    curl_cmd = [
        "curl", "-o", "/tmp/rest_response.json", "-s", "-D", "/tmp/rest_headers.txt",
        "-w", "%{time_namelookup},%{time_connect},%{time_appconnect},%{time_pretransfer},%{time_starttransfer},%{time_total}",
        url
    ]
    
    if method.upper() == "POST":
        curl_cmd.insert(1, "-X")
        curl_cmd.insert(2, "POST")
        if json_data:
            curl_cmd.extend(["-H", "Content-Type: application/json", "-d", json_data])
    elif method.upper() == "DELETE":
        curl_cmd.insert(1, "-X")
        curl_cmd.insert(2, "DELETE")
        if json_data:
            curl_cmd.extend(["-H", "Content-Type: application/json", "-d", json_data])
    
    if headers:
        for header in headers:
            curl_cmd.extend(["-H", header])
    
    result = subprocess.run(
        curl_cmd,
        check=False,
        capture_output=True,
        text=True
    )
    
    # Parse timing
    timings = parse_curl_timing_output(result.stdout)
    
    # Extract database latency
    database_ms = extract_database_ms_from_headers("/tmp/rest_headers.txt")
    if database_ms == 0:
        database_ms = extract_database_ms_from_json("/tmp/rest_response.json")
    
    return {
        **timings,
        'database_ms': database_ms,
        'success': result.returncode == 0
    }


def extract_mcp_timing_fields(result: Any, is_layered: bool = False) -> Dict[str, float]:
    """
    Extract timing fields from MCP response (JSON string or dictionary).
    
    Args:
        result: MCP response (JSON string, dictionary, or wrapped object)
        is_layered: Whether this is a layered MCP response (has rest_ms)
    
    Returns:
        Dictionary with database_ms and optionally rest_ms
    """
    timing_fields = {'database_ms': 0.0}
    if is_layered:
        timing_fields['rest_ms'] = 0.0
    
    try:
        result_json = None
        
        # Handle different result types
        if isinstance(result, str):
            # Try to parse as JSON string
            try:
                result_json = json.loads(result)
            except json.JSONDecodeError:
                # If not JSON, return default (might be plain text)
                return timing_fields
        elif isinstance(result, dict):
            result_json = result
        elif isinstance(result, list) and len(result) > 0:
            # Handle list responses - take first element
            first_item = result[0]
            if isinstance(first_item, dict):
                result_json = first_item
            elif isinstance(first_item, str):
                try:
                    result_json = json.loads(first_item)
                except json.JSONDecodeError:
                    return timing_fields
        elif hasattr(result, 'contents'):
            # Handle ReadResourceResult with .contents attribute (plural)
            contents = result.contents
            if isinstance(contents, list) and len(contents) > 0:
                # Extract text from first content item (TextResourceContents)
                first_content = contents[0]
                if hasattr(first_content, 'text'):
                    # TextResourceContents object
                    try:
                        text_content = first_content.text
                        result_json = json.loads(text_content)
                    except (json.JSONDecodeError, AttributeError):
                        return timing_fields
                elif isinstance(first_content, str):
                    try:
                        result_json = json.loads(first_content)
                    except json.JSONDecodeError:
                        return timing_fields
                elif isinstance(first_content, dict):
                    result_json = first_content
        elif hasattr(result, 'content'):
            # Handle objects with .content attribute (e.g., CallToolResult)
            content = result.content
            if isinstance(content, str):
                try:
                    result_json = json.loads(content)
                except json.JSONDecodeError:
                    return timing_fields
            elif isinstance(content, dict):
                result_json = content
            elif isinstance(content, list) and len(content) > 0:
                # Handle MCP result with content as list of TextContent/ImageContent objects
                # Extract text from first content item
                first_content = content[0]
                if hasattr(first_content, 'text'):
                    # TextContent object
                    try:
                        result_json = json.loads(first_content.text)
                    except (json.JSONDecodeError, AttributeError):
                        return timing_fields
                elif isinstance(first_content, str):
                    try:
                        result_json = json.loads(first_content)
                    except json.JSONDecodeError:
                        return timing_fields
                elif isinstance(first_content, dict):
                    result_json = first_content
        elif hasattr(result, 'text'):
            # Handle objects with .text attribute
            try:
                result_json = json.loads(result.text)
            except (json.JSONDecodeError, AttributeError):
                return timing_fields
        elif hasattr(result, 'result'):
            # Handle objects with .result attribute
            if isinstance(result.result, dict):
                result_json = result.result
            elif isinstance(result.result, str):
                try:
                    result_json = json.loads(result.result)
                except json.JSONDecodeError:
                    return timing_fields
        elif hasattr(result, '__dict__'):
            # Try to access as object attributes
            if hasattr(result, 'database_ms'):
                timing_fields['database_ms'] = float(getattr(result, 'database_ms', 0))
                if is_layered and hasattr(result, 'rest_ms'):
                    timing_fields['rest_ms'] = float(getattr(result, 'rest_ms', 0))
                return timing_fields
        
        # Extract timing fields from parsed JSON
        if result_json is not None:
            if isinstance(result_json, dict):
                timing_fields['database_ms'] = float(result_json.get("database_ms", 0))
                if is_layered:
                    timing_fields['rest_ms'] = float(result_json.get("rest_ms", 0))
    except Exception:
        pass
    
    return timing_fields


def create_timing_dict(request_id: int, connection_ms: float = 0.0, handshake_ms: float = 0.0,
                      resource_read_ms: float = 0.0, tool_call_ms: float = 0.0,
                      total_time_ms: float = 0.0, database_ms: float = 0.0,
                      rest_ms: float = 0.0, status: str = 'failed') -> Dict[str, Any]:
    """Create a standardized timing dictionary."""
    return {
        'request_id': request_id,
        'connection_ms': connection_ms,
        'handshake_ms': handshake_ms,
        'resource_read_ms': resource_read_ms,
        'tool_call_ms': tool_call_ms,
        'total_time_ms': total_time_ms,
        'database_ms': database_ms,
        'rest_ms': rest_ms,
        'status': status
    }

