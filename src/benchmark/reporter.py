"""
Automated chart generator and markdown report generator.
Reads exclusively from actual persisted results.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tabulate import tabulate

from benchmark.config import BenchmarkConfig

logger = logging.getLogger("benchmark.reporter")


class BenchmarkReporter:
    """Generates publication-quality charts and comprehensive markdown reports."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.processed_dir = config.processed_results_dir
        self.charts_dir = config.charts_dir
        self.charts_dir.mkdir(parents=True, exist_ok=True)

        # Style settings
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
        plt.rcParams["font.sans-serif"] = "DejaVu Sans"
        plt.rcParams["font.size"] = 10
        plt.rcParams["axes.titlesize"] = 12
        plt.rcParams["axes.labelsize"] = 10

    def generate_all_charts(self) -> None:
        """Generates all required benchmark visualization charts from actual data."""
        logger.info("Generating benchmark charts from processed results...")
        self._plot_loading_throughput()
        self._plot_traversal_latencies()
        self._plot_lookup_latencies()
        self._plot_aggregation_latency()
        self._plot_concurrency_scaling()
        self._plot_p50_vs_p95()
        logger.info(f"All charts generated in {self.charts_dir}")

    def _plot_loading_throughput(self) -> None:
        csv_path = self.processed_dir / "load_summary.csv"
        if not csv_path.exists():
            logger.warning(f"No loading data found at {csv_path}. Skipping loading chart.")
            return

        df = pd.read_csv(csv_path)
        if df.empty:
            return

        # Group by database taking mean across runs
        agg = df.groupby("database")[["nodes_per_sec", "rels_per_sec"]].mean().reset_index()

        fig, ax = plt.subplots(figsize=(9, 5), dpi=self.config.charts_dir.parent.joinpath("config").exists() and 300 or 150)
        x = np.arange(len(agg))
        width = 0.35

        rects1 = ax.bar(x - width/2, agg["nodes_per_sec"], width, label="Nodes / sec", color="#2b5c8f")
        rects2 = ax.bar(x + width/2, agg["rels_per_sec"], width, label="Relationships / sec", color="#43a047")

        ax.set_ylabel("Records Ingested per Second")
        ax.set_title("Data Ingestion Throughput Comparison")
        ax.set_xticks(x)
        ax.set_xticklabels(agg["database"].str.upper(), fontweight="bold")
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        # Label bars
        for rect in rects1:
            h = rect.get_height()
            ax.annotate(f"{h:,.0f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)
        for rect in rects2:
            h = rect.get_height()
            ax.annotate(f"{h:,.0f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)

        fig.tight_layout()
        out_file = self.charts_dir / "loading_throughput.png"
        fig.savefig(out_file)
        plt.close(fig)

    def _plot_traversal_latencies(self) -> None:
        csv_path = self.processed_dir / "aggregated_summary.csv"
        if not csv_path.exists():
            return

        df = pd.read_csv(csv_path)
        traversal_wls = ["traversal_1_hop", "traversal_2_hop", "traversal_3_hop"]
        df_trav = df[df["workload"].isin(traversal_wls)]

        if df_trav.empty:
            return

        agg = df_trav.groupby(["database", "workload"])[["p50_ms", "p95_ms"]].mean().reset_index()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=150)
        dbs = agg["database"].unique()
        x = np.arange(len(dbs))
        width = 0.25

        for i, wl in enumerate(traversal_wls):
            subset = agg[agg["workload"] == wl]
            val_p50 = [subset[subset["database"] == db]["p50_ms"].values[0] if len(subset[subset["database"] == db]) > 0 else 0 for db in dbs]
            val_p95 = [subset[subset["database"] == db]["p95_ms"].values[0] if len(subset[subset["database"] == db]) > 0 else 0 for db in dbs]

            label = wl.replace("traversal_", "").replace("_", " ").title()
            ax1.bar(x + (i - 1) * width, val_p50, width, label=label)
            ax2.bar(x + (i - 1) * width, val_p95, width, label=label)

        ax1.set_title("Traversal Latency - p50 (Median)")
        ax1.set_ylabel("Latency (ms)")
        ax1.set_xticks(x)
        ax1.set_xticklabels([d.upper() for d in dbs], fontweight="bold")
        ax1.legend()
        ax1.grid(axis="y", linestyle="--", alpha=0.7)

        ax2.set_title("Traversal Latency - p95 (Tail)")
        ax2.set_ylabel("Latency (ms)")
        ax2.set_xticks(x)
        ax2.set_xticklabels([d.upper() for d in dbs], fontweight="bold")
        ax2.legend()
        ax2.grid(axis="y", linestyle="--", alpha=0.7)

        fig.tight_layout()
        out_file = self.charts_dir / "traversal_latencies_1_2_3_hop.png"
        fig.savefig(out_file)
        plt.close(fig)

    def _plot_lookup_latencies(self) -> None:
        csv_path = self.processed_dir / "aggregated_summary.csv"
        if not csv_path.exists():
            return

        df = pd.read_csv(csv_path)
        lookup_wls = ["point_lookup", "filtered_lookup"]
        df_lookup = df[df["workload"].isin(lookup_wls)]

        if df_lookup.empty:
            return

        agg = df_lookup.groupby(["database", "workload"])[["p50_ms", "p95_ms"]].mean().reset_index()

        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
        dbs = agg["database"].unique()
        x = np.arange(len(dbs))
        width = 0.2

        for i, (wl, metric, color) in enumerate([
            ("point_lookup", "p50_ms", "#1e88e5"),
            ("point_lookup", "p95_ms", "#64b5f6"),
            ("filtered_lookup", "p50_ms", "#e53935"),
            ("filtered_lookup", "p95_ms", "#ef9a9a"),
        ]):
            subset = agg[agg["workload"] == wl]
            vals = [subset[subset["database"] == db][metric].values[0] if len(subset[subset["database"] == db]) > 0 else 0 for db in dbs]
            label = f"{wl.replace('_', ' ').title()} ({metric})"
            ax.bar(x + (i - 1.5) * width, vals, width, label=label, color=color)

        ax.set_title("Point Lookup vs. Filtered Lookup Latency")
        ax.set_ylabel("Latency (ms)")
        ax.set_xticks(x)
        ax.set_xticklabels([d.upper() for d in dbs], fontweight="bold")
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        fig.tight_layout()
        out_file = self.charts_dir / "point_and_filtered_lookups.png"
        fig.savefig(out_file)
        plt.close(fig)

    def _plot_aggregation_latency(self) -> None:
        csv_path = self.processed_dir / "aggregated_summary.csv"
        if not csv_path.exists():
            return

        df = pd.read_csv(csv_path)
        df_agg = df[df["workload"] == "aggregation"]
        if df_agg.empty:
            return

        agg = df_agg.groupby("database")[["p50_ms", "p95_ms", "p99_ms"]].mean().reset_index()

        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
        x = np.arange(len(agg))
        width = 0.25

        ax.bar(x - width, agg["p50_ms"], width, label="p50 (Median)", color="#00897b")
        ax.bar(x, agg["p95_ms"], width, label="p95", color="#26a69a")
        ax.bar(x + width, agg["p99_ms"], width, label="p99 (Tail)", color="#80cbc4")

        ax.set_title("Grouped Aggregation Latency")
        ax.set_ylabel("Latency (ms)")
        ax.set_xticks(x)
        ax.set_xticklabels(agg["database"].str.upper(), fontweight="bold")
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        fig.tight_layout()
        out_file = self.charts_dir / "aggregation_latency.png"
        fig.savefig(out_file)
        plt.close(fig)

    def _plot_concurrency_scaling(self) -> None:
        csv_path = self.processed_dir / "mixed_summary.csv"
        if not csv_path.exists():
            return

        df = pd.read_csv(csv_path)
        if df.empty:
            return

        agg = df.groupby(["database", "concurrency"])["throughput_ops_sec"].mean().reset_index()

        fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
        for db, group in agg.groupby("database"):
            group_sorted = group.sort_values("concurrency")
            ax.plot(group_sorted["concurrency"], group_sorted["throughput_ops_sec"], marker="o", linewidth=2.5, label=db.upper())

        ax.set_title("Throughput Scaling across Concurrency Levels (10, 20, 40 Workers)")
        ax.set_xlabel("Concurrent Client Workers")
        ax.set_ylabel("Throughput (Operations / sec)")
        ax.set_xticks([10, 20, 40])
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.7)

        fig.tight_layout()
        out_file = self.charts_dir / "concurrency_scaling.png"
        fig.savefig(out_file)
        plt.close(fig)

    def _plot_p50_vs_p95(self) -> None:
        csv_path = self.processed_dir / "aggregated_summary.csv"
        if not csv_path.exists():
            return

        df = pd.read_csv(csv_path)
        if df.empty:
            return

        agg = df.groupby(["database"])[["p50_ms", "p95_ms"]].mean().reset_index()

        fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
        x = np.arange(len(agg))
        width = 0.35

        ax.bar(x - width/2, agg["p50_ms"], width, label="Overall Average p50", color="#3949ab")
        ax.bar(x + width/2, agg["p95_ms"], width, label="Overall Average p95", color="#f4511e")

        ax.set_title("Overall Average Latency: Median (p50) vs Tail (p95)")
        ax.set_ylabel("Latency (ms)")
        ax.set_xticks(x)
        ax.set_xticklabels(agg["database"].str.upper(), fontweight="bold")
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        fig.tight_layout()
        out_file = self.charts_dir / "p50_vs_p95_comparison.png"
        fig.savefig(out_file)
        plt.close(fig)

    def generate_markdown_report(self) -> Path:
        """Generates comprehensive markdown report summarizing all benchmark results."""
        report_path = self.processed_dir / "benchmark_report.md"

        sections = []
        sections.append("# Graph Database Cloud Benchmarking Report\n")
        sections.append(f"**Generated**: {pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        sections.append("This report presents empirical performance metrics comparing CognDB Cloud, Neo4j, Memgraph, FalkorDB, and Kùzu.\n")

        # 1. Loading Summary
        load_csv = self.processed_dir / "load_summary.csv"
        if load_csv.exists():
            df_load = pd.read_csv(load_csv)
            if not df_load.empty:
                sections.append("## 1. Data Ingestion Performance\n")
                summary_load = df_load.groupby("database").agg({
                    "nodes_loaded": "max",
                    "rels_loaded": "max",
                    "total_load_time_sec": "mean",
                    "nodes_per_sec": "mean",
                    "rels_per_sec": "mean",
                    "total_records_per_sec": "mean"
                }).reset_index()
                sections.append(tabulate(summary_load, headers="keys", tablefmt="github", floatfmt=".2f"))
                sections.append("\n")

        # 2. Workload Latencies
        agg_csv = self.processed_dir / "aggregated_summary.csv"
        if agg_csv.exists():
            df_agg = pd.read_csv(agg_csv)
            if not df_agg.empty:
                sections.append("## 2. Workload Latency Metrics (p50, p90, p95, p99, Throughput)\n")
                summary_agg = df_agg.groupby(["database", "workload"]).agg({
                    "successful_operations": "sum",
                    "failed_operations": "sum",
                    "p50_ms": "mean",
                    "p95_ms": "mean",
                    "p99_ms": "mean",
                    "mean_ms": "mean",
                    "throughput_ops_sec": "mean"
                }).reset_index()
                sections.append(tabulate(summary_agg, headers="keys", tablefmt="github", floatfmt=".3f"))
                sections.append("\n")

        # 3. Mixed Concurrency
        mixed_csv = self.processed_dir / "mixed_summary.csv"
        if mixed_csv.exists():
            df_mixed = pd.read_csv(mixed_csv)
            if not df_mixed.empty:
                sections.append("## 3. Concurrent Multi-Client Mixed Read/Write Scaling\n")
                summary_mixed = df_mixed.groupby(["database", "concurrency"]).agg({
                    "total_operations": "sum",
                    "successful_operations": "sum",
                    "failed_operations": "sum",
                    "throughput_ops_sec": "mean",
                    "read_throughput_ops_sec": "mean",
                    "write_throughput_ops_sec": "mean",
                    "p50_ms": "mean",
                    "p95_ms": "mean",
                    "error_rate": "mean"
                }).reset_index()
                sections.append(tabulate(summary_mixed, headers="keys", tablefmt="github", floatfmt=".2f"))
                sections.append("\n")

        content = "\n".join(sections)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Markdown report generated at {report_path}")
        return report_path
