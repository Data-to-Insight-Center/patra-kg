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


def plot_batch(csv_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path)

    # Construct combined long form for mean and median, with separate hue/style
    long_all = df.melt(
        id_vars=["batch_size", "repeats", "operation"],
        value_vars=["rest_p50_ms", "mcp_p50_ms", "rest_mean_ms", "mcp_mean_ms"],
        var_name="Series",
        value_name="Latency_ms",
    )
    mapping = {
        "rest_p50_ms": ("REST", "Median (p50)"),
        "mcp_p50_ms": ("MCP", "Median (p50)"),
        "rest_mean_ms": ("REST", "Mean"),
        "mcp_mean_ms": ("MCP", "Mean"),
    }
    long_all["System"] = long_all["Series"].map(lambda s: mapping[s][0])
    long_all["Stat"] = long_all["Series"].map(lambda s: mapping[s][1])

    set_pub_style()

    fig, ax = plt.subplots()
    sns.lineplot(
        data=long_all,
        x="batch_size",
        y="Latency_ms",
        hue="System",
        style="Stat",
        markers=True,
        ax=ax,
    )
    ax.set_title("Batch Operation Performance (Mean and Median)")
    ax.set_xlabel("Batch size (number of model cards)")
    ax.set_ylabel("Latency (ms)")
    ax.legend(title="System / Statistic", frameon=True)
    fig.tight_layout()

    png_path = out_dir / "batch_operations.png"
    fig.savefig(png_path)
    plt.close(fig)

    # Mean latency plot (REST vs MCP)
    long_mean = df.melt(
        id_vars=["batch_size", "repeats", "operation"],
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
        x="batch_size",
        y="Latency_ms",
        hue="System",
        marker="o",
        ax=ax2,
    )
    ax2.set_title("Batch Operation Performance (Mean)")
    ax2.set_xlabel("Batch size (number of model cards)")
    ax2.set_ylabel("Latency (ms)")
    ax2.legend(frameon=True)
    fig2.tight_layout()

    png_path_mean = out_dir / "batch_operations_mean.png"
    fig2.savefig(png_path_mean)
    plt.close(fig2)


def main():
    parser = argparse.ArgumentParser(description="Plot batch operations results (standalone)")
    parser.add_argument(
        "--csv",
        default=str(Path.cwd() / "batch_operations.csv"),
        help="Path to batch_operations.csv (default: ./batch_operations.csv)",
    )
    parser.add_argument(
        "--out",
        default=str(Path.cwd()),
        help="Output directory for plots (default: current directory)",
    )
    args = parser.parse_args()

    plot_batch(Path(args.csv), Path(args.out))


if __name__ == "__main__":
    main()


