#!/usr/bin/env python3
"""
Generate LaTeX tables from benchmark CSV files showing mean latency values.
"""

import csv
import statistics
import os
from pathlib import Path


def calculate_means(csv_file):
    """Calculate mean values for all numeric columns in CSV."""
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    # Get all numeric columns (skip request_id, status, http_code)
    numeric_cols = []
    for col in reader.fieldnames:
        if col not in ['request_id', 'status', 'http_code']:
            numeric_cols.append(col)
    
    means = {}
    for col in numeric_cols:
        values = [float(row[col]) for row in data if row[col] and row[col].strip()]
        if values:
            means[col] = statistics.mean(values)
    
    return means


def generate_latex_table_rest_comparison(edge_same, edge_cross, modelcard_same, modelcard_cross):
    """Generate LaTeX table comparing REST API Same Region vs Cross Region."""
    latex = []
    latex.append("\\begin{table}[htbp]")
    latex.append("\\caption{REST API Latency Comparison: Same Region vs Cross Region (Mean Values in ms)}")
    latex.append("\\begin{center}")
    latex.append("\\begin{tabular}{|c|c|c|c|c|}")
    latex.append("\\hline")
    latex.append("\\textbf{Component} & \\multicolumn{2}{|c|}{\\textbf{\\textit{POST /edge}}} & \\multicolumn{2}{|c|}{\\textbf{\\textit{GET /model-card}}} \\\\")
    latex.append("\\cline{2-5}")
    latex.append(" & \\textbf{\\textit{Same}} & \\textbf{\\textit{Cross}} & \\textbf{\\textit{Same}} & \\textbf{\\textit{Cross}} \\\\")
    latex.append(" & \\textbf{\\textit{Region}} & \\textbf{\\textit{Region}} & \\textbf{\\textit{Region}} & \\textbf{\\textit{Region}} \\\\")
    latex.append("\\hline")
    
    # Map REST components
    components = [
        ('DNS Lookup', 'dns_lookup_ms'),
        ('TCP Connection', 'tcp_connect_ms'),
        ('TLS Handshake', 'tls_handshake_ms'),
        ('Time to First Byte', 'time_to_first_byte_ms'),
        ('Total Time', 'total_time_ms')
    ]
    
    for i, (comp_name, col_name) in enumerate(components):
        edge_same_val = edge_same.get(col_name, 0)
        edge_cross_val = edge_cross.get(col_name, 0)
        modelcard_same_val = modelcard_same.get(col_name, 0)
        modelcard_cross_val = modelcard_cross.get(col_name, 0)
        # Add horizontal line before Total Time row
        if comp_name == 'Total Time':
            latex.append("\\hline")
        latex.append(f"{comp_name} & {edge_same_val:.3f} & {edge_cross_val:.3f} & {modelcard_same_val:.3f} & {modelcard_cross_val:.3f} \\\\")
    
    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append("\\label{tab:rest_comparison}")
    latex.append("\\end{center}")
    latex.append("\\end{table}")
    
    return "\n".join(latex)


def generate_latex_table_mcp_comparison(resource_same, resource_cross, tool_same, tool_cross, mcp_type="MCP"):
    """Generate LaTeX table comparing MCP Same Region vs Cross Region."""
    latex = []
    latex.append("\\begin{table}[htbp]")
    latex.append(f"\\caption{{{mcp_type} Latency Comparison: Same Region vs Cross Region (Mean Values in ms)}}")
    latex.append("\\begin{center}")
    latex.append("\\begin{tabular}{|c|c|c|c|c|}")
    latex.append("\\hline")
    latex.append("\\textbf{Component} & \\multicolumn{2}{|c|}{\\textbf{\\textit{MCP Resource Read}}} & \\multicolumn{2}{|c|}{\\textbf{\\textit{MCP Tool Call}}} \\\\")
    latex.append("\\cline{2-5}")
    latex.append(" & \\textbf{\\textit{Same}} & \\textbf{\\textit{Cross}} & \\textbf{\\textit{Same}} & \\textbf{\\textit{Cross}} \\\\")
    latex.append(" & \\textbf{\\textit{Region}} & \\textbf{\\textit{Region}} & \\textbf{\\textit{Region}} & \\textbf{\\textit{Region}} \\\\")
    latex.append("\\hline")
    
    # Map MCP components - resource uses resource_read_ms, tool uses tool_call_ms
    mcp_components = [
        ('Connection Setup', 'connection_ms', 'connection_ms'),
        ('MCP Handshake', 'handshake_ms', 'handshake_ms'),
        ('Resource Read / Tool Call', 'resource_read_ms', 'tool_call_ms'),
        ('Total Time', 'total_time_ms', 'total_time_ms')
    ]
    
    for comp_name, resource_col, tool_col in mcp_components:
        resource_same_val = resource_same.get(resource_col, 0)
        resource_cross_val = resource_cross.get(resource_col, 0)
        tool_same_val = tool_same.get(tool_col, 0)
        tool_cross_val = tool_cross.get(tool_col, 0)
        latex.append(f"{comp_name} & {resource_same_val:.3f} & {resource_cross_val:.3f} & {tool_same_val:.3f} & {tool_cross_val:.3f} \\\\")
    
    latex.append("\\hline")
    latex.append("\\end{tabular}")
    # Generate label based on mcp_type
    label = "native_mcp_comparison" if "Native" in mcp_type else "layered_mcp_comparison" if "Layered" in mcp_type else "mcp_comparison"
    latex.append(f"\\label{{tab:{label}}}")
    latex.append("\\end{center}")
    latex.append("\\end{table}")
    
    return "\n".join(latex)


def generate_latex_table_mcp_resource_read(native_resource_same, native_resource_cross, layered_resource_same, layered_resource_cross):
    """Generate LaTeX table comparing Native MCP and Layered MCP for Resource Read."""
    latex = []
    latex.append("\\begin{table}[htbp]")
    latex.append("\\caption{MCP Resource Read Latency Comparison: Native MCP vs Layered MCP (Mean Values in ms)}")
    latex.append("\\begin{center}")
    latex.append("\\begin{tabular}{|c|c|c|c|c|}")
    latex.append("\\hline")
    latex.append("\\textbf{Component} & \\multicolumn{2}{|c|}{\\textbf{\\textit{Same}}} & \\multicolumn{2}{|c|}{\\textbf{\\textit{Cross}}} \\\\")
    latex.append("\\cline{2-5}")
    latex.append(" & \\textbf{\\textit{Native}} & \\textbf{\\textit{Layered}} & \\textbf{\\textit{Native}} & \\textbf{\\textit{Layered}} \\\\")
    latex.append("\\hline")
    
    # Map MCP components - resource uses resource_read_ms
    mcp_components = [
        ('Connection Setup', 'connection_ms'),
        ('MCP Handshake', 'handshake_ms'),
        ('Operation', 'resource_read_ms'),
        ('Total Time', 'total_time_ms')
    ]
    
    for comp_name, col_name in mcp_components:
        native_same_val = native_resource_same.get(col_name, 0)
        native_cross_val = native_resource_cross.get(col_name, 0)
        layered_same_val = layered_resource_same.get(col_name, 0)
        layered_cross_val = layered_resource_cross.get(col_name, 0)
        # Add horizontal line before Total Time row
        if comp_name == 'Total Time':
            latex.append("\\hline")
        latex.append(f"{comp_name} & {native_same_val:.3f} & {layered_same_val:.3f} & {native_cross_val:.3f} & {layered_cross_val:.3f} \\\\")
    
    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append("\\label{tab:mcp_resource_read_comparison}")
    latex.append("\\end{center}")
    latex.append("\\end{table}")
    
    return "\n".join(latex)


def generate_latex_table_mcp_tool_call(native_tool_same, native_tool_cross, layered_tool_same, layered_tool_cross):
    """Generate LaTeX table comparing Native MCP and Layered MCP for Tool Call."""
    latex = []
    latex.append("\\begin{table}[htbp]")
    latex.append("\\caption{MCP Tool Call Latency Comparison: Native MCP vs Layered MCP (Mean Values in ms)}")
    latex.append("\\begin{center}")
    latex.append("\\begin{tabular}{|c|c|c|c|c|}")
    latex.append("\\hline")
    latex.append("\\textbf{Component} & \\multicolumn{2}{|c|}{\\textbf{\\textit{Same}}} & \\multicolumn{2}{|c|}{\\textbf{\\textit{Cross}}} \\\\")
    latex.append("\\cline{2-5}")
    latex.append(" & \\textbf{\\textit{Native}} & \\textbf{\\textit{Layered}} & \\textbf{\\textit{Native}} & \\textbf{\\textit{Layered}} \\\\")
    latex.append("\\hline")
    
    # Map MCP components - tool uses tool_call_ms
    mcp_components = [
        ('Connection Setup', 'connection_ms'),
        ('MCP Handshake', 'handshake_ms'),
        ('Operation', 'tool_call_ms'),
        ('Total Time', 'total_time_ms')
    ]
    
    for comp_name, col_name in mcp_components:
        native_same_val = native_tool_same.get(col_name, 0)
        native_cross_val = native_tool_cross.get(col_name, 0)
        layered_same_val = layered_tool_same.get(col_name, 0)
        layered_cross_val = layered_tool_cross.get(col_name, 0)
        # Add horizontal line before Total Time row
        if comp_name == 'Total Time':
            latex.append("\\hline")
        latex.append(f"{comp_name} & {native_same_val:.3f} & {layered_same_val:.3f} & {native_cross_val:.3f} & {layered_cross_val:.3f} \\\\")
    
    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append("\\label{tab:mcp_tool_call_comparison}")
    latex.append("\\end{center}")
    latex.append("\\end{table}")
    
    return "\n".join(latex)


def generate_latex_table_complete_comparison(rest_edge, rest_modelcard, stacked, native):
    """Generate LaTeX table with complete comparison of all benchmarks."""
    latex = []
    latex.append("\\begin{table}[htbp]")
    latex.append("\\caption{Complete Latency Breakdown Comparison (Mean Values in ms)}")
    latex.append("\\begin{center}")
    latex.append("\\begin{tabular}{|c|c|c|c|c|}")
    latex.append("\\hline")
    latex.append("\\textbf{Component} & \\textbf{\\textit{REST Edge}} & \\textbf{\\textit{REST ModelCard}} & \\textbf{\\textit{Stacked MCP}} & \\textbf{\\textit{Native MCP}} \\\\")
    latex.append("\\hline")
    
    # Combine all components
    all_components = [
        ('DNS Lookup', 'dns_lookup_ms', None, None, None),
        ('TCP Connection', 'tcp_connect_ms', None, None, None),
        ('TLS Handshake', 'tls_handshake_ms', None, None, None),
        ('Connection Setup', None, None, 'connection_ms', 'connection_ms'),
        ('MCP Handshake', None, None, 'handshake_ms', 'handshake_ms'),
        ('Resource Read', None, None, 'resource_read_ms', 'resource_read_ms'),
        ('Time to First Byte', 'time_to_first_byte_ms', 'time_to_first_byte_ms', None, None),
        ('Total Time', 'total_time_ms', 'total_time_ms', 'total_time_ms', 'total_time_ms')
    ]
    
    for comp_name, rest_edge_col, rest_mc_col, stacked_col, native_col in all_components:
        re_val = rest_edge.get(rest_edge_col, 0) if rest_edge_col else None
        rm_val = rest_modelcard.get(rest_mc_col, 0) if rest_mc_col else None
        s_val = stacked.get(stacked_col, 0) if stacked_col else None
        n_val = native.get(native_col, 0) if native_col else None
        
        # Format values
        re_str = f"{re_val:.3f}" if isinstance(re_val, (int, float)) else "-"
        rm_str = f"{rm_val:.3f}" if isinstance(rm_val, (int, float)) else "-"
        s_str = f"{s_val:.3f}" if isinstance(s_val, (int, float)) else "-"
        n_str = f"{n_val:.3f}" if isinstance(n_val, (int, float)) else "-"
        
        latex.append(f"{comp_name} & {re_str} & {rm_str} & {s_str} & {n_str} \\\\")
    
    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append("\\label{tab:complete_comparison}")
    latex.append("\\end{center}")
    latex.append("\\end{table}")
    
    return "\n".join(latex)


def main():
    """Main function to generate all LaTeX tables."""
    # File paths - Same Region (local/) vs Cross Region (root)
    base_dir = Path(__file__).parent
    files = {
        # REST - Same Region
        'REST Edge Same': base_dir / 'local' / 'rest' / 'curl_edge_timing_results.csv',
        'REST ModelCard Same': base_dir / 'local' / 'rest' / 'curl_timing_results.csv',
        # REST - Cross Region
        'REST Edge Cross': base_dir / 'rest' / 'curl_edge_timing_results.csv',
        'REST ModelCard Cross': base_dir / 'rest' / 'curl_timing_results.csv',
        # MCP Resource Read - Same Region
        'MCP Resource Same': base_dir / 'local' / 'mcp' / 'native_mcp_timing_results.csv',
        # MCP Resource Read - Cross Region
        'MCP Resource Cross': base_dir / 'mcp' / 'native_mcp_timing_results.csv',
        # MCP Tool Call - Same Region
        'MCP Tool Same': base_dir / 'local' / 'mcp' / 'native_mcp_edge_timing_results.csv',
        # MCP Tool Call - Cross Region
        'MCP Tool Cross': base_dir / 'mcp' / 'native_mcp_edge_timing_results.csv',
        # Layered MCP Resource Read - Same Region
        'Layered MCP Resource Same': base_dir / 'local' / 'mcp' / 'mcp_timing_results.csv',
        # Layered MCP Resource Read - Cross Region
        'Layered MCP Resource Cross': base_dir / 'mcp' / 'mcp_timing_results.csv',
        # Layered MCP Tool Call - Same Region
        'Layered MCP Tool Same': base_dir / 'local' / 'mcp' / 'mcp_edge_timing_results.csv',
        # Layered MCP Tool Call - Cross Region
        'Layered MCP Tool Cross': base_dir / 'mcp' / 'mcp_edge_timing_results.csv'
    }
    
    # Calculate means for each file
    results = {}
    for name, path in files.items():
        try:
            if path.exists():
                results[name] = calculate_means(str(path))
                print(f"✓ Loaded {name}: {len(results[name])} components")
            else:
                print(f"✗ File not found: {path}")
        except Exception as e:
            print(f"✗ Error processing {name}: {e}")
    
    if not results:
        print("No data files found. Exiting.")
        return
    
    # Generate LaTeX tables
    print("\n" + "="*80)
    print("GENERATED LATEX TABLES")
    print("="*80)
    
    # Table 1: REST Comparison (POST /edge and GET /model-card: Same vs Cross Region)
    if all(key in results for key in ['REST Edge Same', 'REST Edge Cross', 'REST ModelCard Same', 'REST ModelCard Cross']):
        print("\n" + "-"*80)
        print("Table 1: REST API Comparison (Same Region vs Cross Region)")
        print("-"*80)
        table1 = generate_latex_table_rest_comparison(
            results['REST Edge Same'],
            results['REST Edge Cross'],
            results['REST ModelCard Same'],
            results['REST ModelCard Cross']
        )
        print(table1)
    
    # Table 2: MCP Resource Read Comparison (Native MCP vs Layered MCP)
    if all(key in results for key in ['MCP Resource Same', 'MCP Resource Cross', 'Layered MCP Resource Same', 'Layered MCP Resource Cross']):
        print("\n" + "-"*80)
        print("Table 2: MCP Resource Read Comparison (Native MCP vs Layered MCP)")
        print("-"*80)
        table2 = generate_latex_table_mcp_resource_read(
            results['MCP Resource Same'],
            results['MCP Resource Cross'],
            results['Layered MCP Resource Same'],
            results['Layered MCP Resource Cross']
        )
        print(table2)
    
    # Table 3: MCP Tool Call Comparison (Native MCP vs Layered MCP)
    if all(key in results for key in ['MCP Tool Same', 'MCP Tool Cross', 'Layered MCP Tool Same', 'Layered MCP Tool Cross']):
        print("\n" + "-"*80)
        print("Table 3: MCP Tool Call Comparison (Native MCP vs Layered MCP)")
        print("-"*80)
        table3 = generate_latex_table_mcp_tool_call(
            results['MCP Tool Same'],
            results['MCP Tool Cross'],
            results['Layered MCP Tool Same'],
            results['Layered MCP Tool Cross']
        )
        print(table3)
    
    # Optionally save to file
    output_file = base_dir / 'latex_tables.tex'
    with open(output_file, 'w') as f:
        if all(key in results for key in ['REST Edge Same', 'REST Edge Cross', 'REST ModelCard Same', 'REST ModelCard Cross']):
            f.write(generate_latex_table_rest_comparison(
                results['REST Edge Same'],
                results['REST Edge Cross'],
                results['REST ModelCard Same'],
                results['REST ModelCard Cross']
            ))
            f.write("\n\n")
        
        if all(key in results for key in ['MCP Resource Same', 'MCP Resource Cross', 'Layered MCP Resource Same', 'Layered MCP Resource Cross']):
            f.write(generate_latex_table_mcp_resource_read(
                results['MCP Resource Same'],
                results['MCP Resource Cross'],
                results['Layered MCP Resource Same'],
                results['Layered MCP Resource Cross']
            ))
            f.write("\n\n")
        
        if all(key in results for key in ['MCP Tool Same', 'MCP Tool Cross', 'Layered MCP Tool Same', 'Layered MCP Tool Cross']):
            f.write(generate_latex_table_mcp_tool_call(
                results['MCP Tool Same'],
                results['MCP Tool Cross'],
                results['Layered MCP Tool Same'],
                results['Layered MCP Tool Cross']
            ))
    
    print(f"\n✓ LaTeX tables saved to: {output_file}")


if __name__ == "__main__":
    main()

