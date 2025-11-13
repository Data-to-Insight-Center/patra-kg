#!/bin/bash

# Configuration
URL="http://149.165.175.102:5002/modelcard/megadetector-mc-9aaede5b"
NUM_REQUESTS=100
OUTPUT_FILE="curl_timing_results.txt"
CSV_FILE="curl_timing_results.csv"

# Clear output files
> "$OUTPUT_FILE"
> "$CSV_FILE"

echo "Running $NUM_REQUESTS curl requests with timing breakdown..."
echo "Results will be saved to: $OUTPUT_FILE and $CSV_FILE"
echo ""

# Header for text file
echo "==================================================================" >> "$OUTPUT_FILE"
echo "Curl Timing Breakdown - $NUM_REQUESTS Requests" >> "$OUTPUT_FILE"
echo "URL: $URL" >> "$OUTPUT_FILE"
echo "Date: $(date)" >> "$OUTPUT_FILE"
echo "==================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Header for CSV file
echo "request_id,dns_lookup_ms,tcp_connect_ms,tls_handshake_ms,time_pretransfer_ms,time_to_first_byte_ms,total_time_ms,http_code" >> "$CSV_FILE"

# Warm-up phase
echo "Running warm-up phase (10 requests)..."
for i in $(seq 1 10); do
    echo -n "Warm-up request $i/10... "
    curl -o /dev/null -s "$URL" > /dev/null 2>&1
    echo "Done"
done
echo "Warm-up complete! Starting measurements..."
echo ""

# Run requests
for i in $(seq 1 $NUM_REQUESTS); do
    echo -n "Request $i/$NUM_REQUESTS... "
    
    # Capture timing metrics
    timing_output=$(curl -o /dev/null -s -w "%{time_namelookup},%{time_connect},%{time_appconnect},%{time_pretransfer},%{time_starttransfer},%{time_total},%{http_code}" "$URL")
    
    # Parse output
    IFS=',' read -r dns_lookup tcp_connect tls_handshake time_pretransfer ttfb total_time http_code <<< "$timing_output"
    
    # Convert to milliseconds using awk
    dns_lookup_ms=$(awk "BEGIN {printf \"%.3f\", $dns_lookup * 1000}")
    tcp_connect_ms=$(awk "BEGIN {printf \"%.3f\", $tcp_connect * 1000}")
    tls_handshake_ms=$(awk "BEGIN {printf \"%.3f\", $tls_handshake * 1000}")
    time_pretransfer_ms=$(awk "BEGIN {printf \"%.3f\", $time_pretransfer * 1000}")
    ttfb_ms=$(awk "BEGIN {printf \"%.3f\", $ttfb * 1000}")
    total_time_ms=$(awk "BEGIN {printf \"%.3f\", $total_time * 1000}")
    
    # Write to text file
    echo "--- Request $i ---" >> "$OUTPUT_FILE"
    echo "DNS Lookup:            $dns_lookup_ms ms" >> "$OUTPUT_FILE"
    echo "TCP Connection:        $tcp_connect_ms ms" >> "$OUTPUT_FILE"
    echo "TLS Handshake:         $tls_handshake_ms ms" >> "$OUTPUT_FILE"
    echo "Time to Request Sent:  $time_pretransfer_ms ms" >> "$OUTPUT_FILE"
    echo "Time to First Byte:    $ttfb_ms ms" >> "$OUTPUT_FILE"
    echo "Total Time:            $total_time_ms ms" >> "$OUTPUT_FILE"
    echo "HTTP Code:             $http_code" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Write to CSV file
    echo "$i,$dns_lookup_ms,$tcp_connect_ms,$tls_handshake_ms,$time_pretransfer_ms,$ttfb_ms,$total_time_ms,$http_code" >> "$CSV_FILE"
    
    echo "Done"
done

echo "" >> "$OUTPUT_FILE"
echo "==================================================================" >> "$OUTPUT_FILE"
echo "Benchmark Complete!" >> "$OUTPUT_FILE"
echo "==================================================================" >> "$OUTPUT_FILE"

echo ""
echo "Benchmark complete!"
echo "Results saved to:"
echo "  - Text format: $OUTPUT_FILE"
echo "  - CSV format:  $CSV_FILE"
