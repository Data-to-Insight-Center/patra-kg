#!/usr/bin/env python3
"""
Side-by-side stacked bar plot comparing REST, Native MCP, and Stacked MCP edge creation latency breakdowns.
Ignores latency components < 5ms for cleaner publication-ready plots.
Labels are displayed directly on bars with black text on light backgrounds.
Same components use consistent colors and hatch patterns across all bars for easy identification.
Uses lighter/pastel colors with distinct hatch patterns for better printability.
"""

import csv
import statistics
import os
import matplotlib.pyplot as plt
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

plt.rcParams.update({
    # Font settings - professional serif fonts
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'Computer Modern Roman'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 13,

    # Figure quality and output
    'figure.dpi': 100,
    'figure.facecolor': 'white',
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'savefig.format': 'png',
    'savefig.facecolor': 'white',
    'savefig.edgecolor': 'none',

    # Grid settings - subtle and professional
    'grid.alpha': 0.25,
    'grid.linewidth': 0.5,
    'grid.color': '#cccccc',
    'grid.linestyle': '-',

    # Axis settings - clean and minimal
    'axes.linewidth': 0.8,
    'axes.edgecolor': '#333333',
    'axes.labelcolor': '#333333',
    'axes.grid': True,
    'axes.axisbelow': True,
    'axes.facecolor': 'white',

    # Tick settings
    'xtick.color': '#333333',
    'ytick.color': '#333333',
    'xtick.direction': 'out',
    'ytick.direction': 'out',

    # Legend settings - professional appearance
    'legend.frameon': True,
    'legend.edgecolor': '#cccccc',
    'legend.fancybox': False,
    'legend.shadow': False,

    # Use LaTeX-style math rendering
    'mathtext.default': 'regular',
})

# Color scheme - lighter colors with patterns for better distinction
COLORS = {
    'black': '#000000',      # Primary text/borders
    'white': '#ffffff',      # Background
    # Component-specific colors - lighter/pastel tones
    'dns': '#D6EAF8',            # Very light blue - DNS Lookup
    'tcp': '#FFE6CC',            # Very light orange - TCP Connection
    'tls': '#D5F4E6',            # Very light green - TLS Handshake
    'connection': '#D6EAF8',     # Very light blue - Connection Setup (same as DNS)
    'handshake': '#FFE6CC',      # Very light orange - MCP Handshake (same as TCP)
    'tool_call': '#D5F4E6',      # Very light green - Tool Call (same as TLS)
    'server': '#FADBD8',         # Very light red - Server Overhead
    'transfer': '#E8DAEF',       # Very light purple - Content Transfer
    'rest_overhead': '#FADBD8',  # Very light red - REST Overhead (same as Server)
    'db': '#EDBB99',             # Very light brown - Database Overhead (consistent across all)
}

# Hatch patterns for each component - simple and distinct
PATTERNS = {
    'dns': '/',
    'tcp': '\\',
    'tls': 'o',
    'connection': '/',           # Same as DNS
    'handshake': '\\',           # Same as TCP
    'tool_call': 'o',           # Same as TLS
    'server': '+',
    'transfer': 'x',
    'rest_overhead': '+',        # Same as Server
    'db': '.',
}


# =============================================================================
# DATA LOADING AND ANALYSIS
# =============================================================================

def load_and_analyze_data(csv_file='curl_edge_timing_results.csv', db_file='db.csv'):
    """Load CSV data and calculate statistics."""
    # Handle paths relative to script location or current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(csv_file):
        csv_file = os.path.join(script_dir, csv_file)
    if not os.path.exists(db_file):
        db_file = os.path.join(script_dir, db_file)
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Extract metrics
    dns_lookups = [float(row['dns_lookup_ms']) for row in data]
    tcp_connects = [float(row['tcp_connect_ms']) for row in data]
    tls_handshakes = [float(row['tls_handshake_ms']) for row in data]
    time_pretransfers = [float(row['time_pretransfer_ms']) for row in data]
    ttfbs = [float(row['time_to_first_byte_ms']) for row in data]
    total_times = [float(row['total_time_ms']) for row in data]

    # Calculate derived metrics
    tcp_only = [tcp_connects[i] - dns_lookups[i] for i in range(len(data))]
    server_processing = [ttfbs[i] - time_pretransfers[i] for i in range(len(data))]
    content_transfer = [total_times[i] - ttfbs[i] for i in range(len(data))]

    # Load Database Overhead if available
    db_latencies = []
    try:
        with open(db_file, 'r') as f:
            db_latencies = [float(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: {db_file} not found, skipping Database Overhead overlay")

    components = {
        'DNS Lookup': dns_lookups,
        'TCP Connection': tcp_only,
        'TLS Handshake': tls_handshakes,
        'Server Overhead': server_processing,
        'Content Transfer': content_transfer,
    }

    if db_latencies:
        components['Database Overhead'] = db_latencies

    # Calculate statistics
    stats = {}
    for name, values in components.items():
        stats[name] = {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'p95': sorted(values)[int(len(values) * 0.95)],
        }

    return stats

def load_and_analyze_mcp_data(csv_file='../mcp/mcp_edge_timing_results.csv', db_file='../mcp/layered_mcp_db.csv', rest_file='../mcp/layered_mcp_rest.csv'):
    """Load MCP CSV data and calculate statistics."""
    # Handle paths relative to script location or current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(csv_file):
        csv_file = os.path.join(script_dir, csv_file)
    if not os.path.exists(db_file):
        db_file = os.path.join(script_dir, db_file)
    if not os.path.exists(rest_file):
        rest_file = os.path.join(script_dir, rest_file)
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Extract metrics
    connections = [float(row['connection_ms']) for row in data]
    handshakes = [float(row['handshake_ms']) for row in data]
    tool_calls = [float(row['tool_call_ms']) for row in data]

    # Load REST Overhead if available
    rest_latencies = []
    try:
        with open(rest_file, 'r') as f:
            rest_latencies = [float(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: {rest_file} not found, skipping REST Overhead overlay")

    # Load Database Overhead if available
    db_latencies = []
    try:
        with open(db_file, 'r') as f:
            db_latencies = [float(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: {db_file} not found, skipping Database Overhead overlay")

    components = {
        'Connection Setup': connections,
        'MCP Handshake': handshakes,
        'Tool Call': tool_calls,
    }

    if rest_latencies:
        components['REST Overhead'] = rest_latencies

    if db_latencies:
        components['Database Overhead'] = db_latencies

    # Calculate statistics
    stats = {}
    for name, values in components.items():
        stats[name] = {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'p95': sorted(values)[int(len(values) * 0.95)],
        }

    return stats

def load_and_analyze_native_mcp_data(csv_file='../mcp/native_mcp_edge_timing_results.csv', db_file='../mcp/native_mcp_db.csv'):
    """Load Native MCP CSV data and calculate statistics."""
    # Handle paths relative to script location or current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(csv_file):
        csv_file = os.path.join(script_dir, csv_file)
    if not os.path.exists(db_file):
        db_file = os.path.join(script_dir, db_file)
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Extract metrics
    connections = [float(row['connection_ms']) for row in data]
    handshakes = [float(row['handshake_ms']) for row in data]
    tool_calls = [float(row['tool_call_ms']) for row in data]

    # Load database latency if available
    db_latencies = []
    try:
        with open(db_file, 'r') as f:
            db_latencies = [float(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: {db_file} not found, skipping Database Overhead overlay")

    components = {
        'Connection Setup': connections,
        'MCP Handshake': handshakes,
        'Tool Call': tool_calls,
    }

    if db_latencies:
        components['Database Overhead'] = db_latencies

    # Calculate statistics
    stats = {}
    for name, values in components.items():
        stats[name] = {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'p95': sorted(values)[int(len(values) * 0.95)],
        }

    return stats

# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def create_comparison_plot(rest_stats, stacked_mcp_stats, native_mcp_stats, output_path='edge_latency_comparison.png'):
    """Create side-by-side stacked bar plots comparing REST, Native MCP, and Stacked MCP latency breakdowns."""

    fig, ax = plt.subplots(figsize=(5, 3.5))

    # Define REST components - each component has its own color and pattern
    # Using 2-line labels for better fit
    rest_components = [
        ('DNS Lookup', 'DNS\nLookup', COLORS['dns'], PATTERNS['dns']),
        ('TCP Connection', 'TCP\nConnection', COLORS['tcp'], PATTERNS['tcp']),
        ('TLS Handshake', 'TLS\nHandshake', COLORS['tls'], PATTERNS['tls']),
        ('Server Overhead', 'Server\nOverhead', COLORS['server'], PATTERNS['server']),
        ('Content Transfer', 'Content\nTransfer', COLORS['transfer'], PATTERNS['transfer']),
    ]
    if 'Database Overhead' in rest_stats:
        rest_components.insert(4, ('Database Overhead', 'Database\nOverhead', COLORS['db'], PATTERNS['db']))

    # Define Native MCP components - each component has its own color and pattern
    # Using 2-line labels for better fit
    native_mcp_components = [
        ('Connection Setup', 'Connection\nSetup', COLORS['connection'], PATTERNS['connection']),
        ('MCP Handshake', 'MCP\nHandshake', COLORS['handshake'], PATTERNS['handshake']),
        ('Tool Call', 'Tool\nCall', COLORS['tool_call'], PATTERNS['tool_call']),
    ]
    if 'Database Overhead' in native_mcp_stats:
        native_mcp_components.append(('Database Overhead', 'Database\nOverhead', COLORS['db'], PATTERNS['db']))

    # Define Stacked MCP components - each component has its own color and pattern
    # Using 2-line labels for better fit
    stacked_mcp_components = [
        ('Connection Setup', 'Connection\nSetup', COLORS['connection'], PATTERNS['connection']),
        ('MCP Handshake', 'MCP\nHandshake', COLORS['handshake'], PATTERNS['handshake']),
        ('Tool Call', 'Tool\nCall', COLORS['tool_call'], PATTERNS['tool_call']),
    ]
    if 'REST Overhead' in stacked_mcp_stats:
        stacked_mcp_components.append(('REST Overhead', 'REST\nOverhead', COLORS['rest_overhead'], PATTERNS['rest_overhead']))
    if 'Database Overhead' in stacked_mcp_stats:
        stacked_mcp_components.append(('Database Overhead', 'Database\nOverhead', COLORS['db'], PATTERNS['db']))

    # Filter REST components >= 5ms
    rest_significant = []
    for label, display_label, color, pattern in rest_components:
        if label in rest_stats:
            duration = rest_stats[label]['mean']
            if duration >= 5.0:
                rest_significant.append((display_label, color, pattern, duration))

    # Filter Native MCP components >= 5ms
    native_mcp_significant = []
    for label, display_label, color, pattern in native_mcp_components:
        if label in native_mcp_stats:
            duration = native_mcp_stats[label]['mean']
            if duration >= 5.0:
                native_mcp_significant.append((display_label, color, pattern, duration))

    # Filter Stacked MCP components >= 5ms
    stacked_mcp_significant = []
    for label, display_label, color, pattern in stacked_mcp_components:
        if label in stacked_mcp_stats:
            duration = stacked_mcp_stats[label]['mean']
            if duration >= 5.0:
                stacked_mcp_significant.append((display_label, color, pattern, duration))

    # Helper function to create next darker shade
    def next_shade(hex_color, factor=0.93):
        """Create a slightly darker shade of the color for patterns."""
        import matplotlib.colors as mcolors
        rgb = mcolors.hex2color(hex_color)
        darker = tuple(c * factor for c in rgb)
        return darker

    # Create REST stacked bar
    bar_width = 0.25
    rest_x = 0
    bottom = 0
    for display_label, color, pattern, height in rest_significant:
        # Pattern uses slightly darker shade of fill color
        ax.bar(rest_x, height, bottom=bottom, color=color,
              edgecolor=next_shade(color), linewidth=1.0, alpha=1.0,
              width=bar_width, hatch=pattern)

        # Add text label on the bar - single line if < 100ms, two lines otherwise
        label_text = display_label.replace('\n', ' ') if height < 100 else display_label
        ax.text(rest_x, bottom + height/2, label_text,
               ha='center', va='center', fontsize=6, fontweight='bold',
               color=COLORS['black'])

        bottom += height

    # Create Native MCP bar (next to REST)
    native_mcp_x = 0.35
    bottom = 0
    for display_label, color, pattern, height in native_mcp_significant:
        # Pattern uses slightly darker shade of fill color
        ax.bar(native_mcp_x, height, bottom=bottom, color=color,
              edgecolor=next_shade(color), linewidth=1.0, alpha=1.0,
              width=bar_width, hatch=pattern)

        # Add text label on the bar - single line if < 100ms, two lines otherwise
        label_text = display_label.replace('\n', ' ') if height < 100 else display_label
        ax.text(native_mcp_x, bottom + height/2, label_text,
               ha='center', va='center', fontsize=6, fontweight='bold',
               color=COLORS['black'])

        bottom += height

    # Create Stacked MCP bar
    stacked_mcp_x = 0.7
    bottom = 0
    for display_label, color, pattern, height in stacked_mcp_significant:
        # Pattern uses slightly darker shade of fill color
        ax.bar(stacked_mcp_x, height, bottom=bottom, color=color,
              edgecolor=next_shade(color), linewidth=1.0, alpha=1.0,
              width=bar_width, hatch=pattern)

        # Add text label on the bar - single line if < 100ms, two lines otherwise
        label_text = display_label.replace('\n', ' ') if height < 100 else display_label
        ax.text(stacked_mcp_x, bottom + height/2, label_text,
               ha='center', va='center', fontsize=6, fontweight='bold',
               color=COLORS['black'])

        bottom += height

    # Configure axes
    ax.set_xticks([rest_x, native_mcp_x, stacked_mcp_x])
    ax.set_xticklabels(['REST', 'Native MCP', 'Stacked MCP'], fontsize=10, fontweight='bold')
    ax.set_ylabel('Latency (ms)', fontsize=10, fontweight='bold')

    # Set y-axis limit with some padding
    max_height = max(
        sum(h for _, _, _, h in rest_significant),
        sum(h for _, _, _, h in native_mcp_significant),
        sum(h for _, _, _, h in stacked_mcp_significant)
    )
    ax.set_ylim(0, max_height * 1.1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Comparison plot saved to: {output_path}")
    plt.close()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    print("="*80)
    print("Creating REST vs Stacked MCP vs Native MCP Edge Creation Latency Comparison Plot")
    print("="*80)

    # Load and analyze REST data
    print("\nLoading REST data...")
    rest_stats = load_and_analyze_data()

    # Load and analyze Stacked MCP data
    print("Loading Stacked MCP data...")
    stacked_mcp_stats = load_and_analyze_mcp_data()

    # Load and analyze Native MCP data
    print("Loading Native MCP data...")
    native_mcp_stats = load_and_analyze_native_mcp_data()

    # Create comparison plot
    output_file = 'edge_latency_comparison.png'
    create_comparison_plot(rest_stats, stacked_mcp_stats, native_mcp_stats, output_file)

    print("\n" + "="*80)
    print("Visualization created successfully!")
    print("="*80)
    print(f"\nGenerated file: {output_file}")

if __name__ == "__main__":
    main()

