import argparse
from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def set_pub_style():
    sns.set_theme(context="talk", style="whitegrid")
    plt.rcParams.update({
        "figure.figsize": (10, 6),
        "axes.titlesize": 22,
        "axes.labelsize": 16,
        "legend.fontsize": 14,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "lines.linewidth": 2.0,
        "savefig.dpi": 300,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def plot_workflow(csv_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path)

    set_pub_style()

    # Median plot (p50)
    long_p50 = df.melt(
        id_vars=["limit", "repeats", "operation"],
        value_vars=["rest_p50_ms", "mcp_p50_ms"],
        var_name="System",
        value_name="Latency_ms",
    )
    long_p50["System"] = long_p50["System"].map({
        "rest_p50_ms": "REST (p50)",
        "mcp_p50_ms": "MCP (p50)",
    })

    fig1, ax1 = plt.subplots()
    sns.lineplot(
        data=long_p50,
        x="limit",
        y="Latency_ms",
        hue="System",
        marker="o",
        ax=ax1,
    )
    ax1.set_title("Workflow Performance (Median)")
    ax1.set_xlabel("Workflow size (list+get N cards)")
    ax1.set_ylabel("Latency (ms)")
    ax1.legend(frameon=True)

    # Annotate MCP advantage percentages near MCP p50 points
    try:
        for row in df.itertuples():
            ax1.text(
                float(row.limit),
                float(row.mcp_p50_ms),
                f"{float(row.mcp_advantage_pct):.1f}%",
                fontsize=12,
                ha="left",
                va="bottom",
            )
    except Exception:
        pass

    fig1.tight_layout()
    fig1.savefig(out_dir / "workflow_operations.png")
    plt.close(fig1)

    # Mean plot
    long_mean = df.melt(
        id_vars=["limit", "repeats", "operation"],
        value_vars=["rest_mean_ms", "mcp_mean_ms"],
        var_name="System",
        value_name="Latency_ms",
    )
    long_mean["System"] = long_mean["System"].map({
        "rest_mean_ms": "REST (mean)",
        "mcp_mean_ms": "MCP (mean)",
    })

    fig2, ax2 = plt.subplots()
    sns.lineplot(
        data=long_mean,
        x="limit",
        y="Latency_ms",
        hue="System",
        marker="o",
        ax=ax2,
    )
    ax2.set_title("Workflow Performance (Mean)")
    ax2.set_xlabel("Workflow size (list+get N cards)")
    ax2.set_ylabel("Latency (ms)")
    ax2.legend(frameon=True)
    fig2.tight_layout()
    fig2.savefig(out_dir / "workflow_operations_mean.png")
    plt.close(fig2)


def main():
    parser = argparse.ArgumentParser(description="Plot workflow operations results (standalone)")
    parser.add_argument(
        "--csv",
        default=str(Path.cwd() / "workflow_operations.csv"),
        help="Path to workflow_operations.csv (default: ./workflow_operations.csv)",
    )
    parser.add_argument(
        "--out",
        default=str(Path.cwd()),
        help="Output directory for plots (default: current directory)",
    )
    args = parser.parse_args()

    plot_workflow(Path(args.csv), Path(args.out))


if __name__ == "__main__":
    main()


