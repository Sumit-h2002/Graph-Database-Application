"""
Statistical calculation and result persistence engine.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from benchmark.models import (
    AggregatedResult,
    BenchmarkResult,
    LoadResult,
    MixedWorkloadResult,
    ResourceMetric,
)

logger = logging.getLogger("benchmark.statistics")


def calculate_aggregated_result(
    raw_results: List[BenchmarkResult],
    total_elapsed_sec: Optional[float] = None
) -> AggregatedResult:
    """
    Computes statistical percentiles and error metrics from raw measurements.
    """
    if not raw_results:
        raise ValueError("Cannot calculate statistics on empty raw results list.")

    database = raw_results[0].database
    workload = raw_results[0].workload
    run_id = raw_results[0].run_id
    total_iterations = len(raw_results)

    successful = [r for r in raw_results if r.success and r.latency_ms is not None]
    failed = [r for r in raw_results if not r.success]

    successful_ops = len(successful)
    failed_ops = len(failed)

    error_breakdown: Dict[str, int] = {}
    for r in failed:
        err = r.error_type or "UnknownError"
        error_breakdown[err] = error_breakdown.get(err, 0) + 1

    if successful:
        latencies = np.array([r.latency_ms for r in successful], dtype=np.float64)
        p50 = float(np.percentile(latencies, 50))
        p90 = float(np.percentile(latencies, 90))
        p95 = float(np.percentile(latencies, 95))
        p99 = float(np.percentile(latencies, 99))
        mean = float(np.mean(latencies))
        min_v = float(np.min(latencies))
        max_v = float(np.max(latencies))
        std = float(np.std(latencies))

        # Throughput
        if total_elapsed_sec and total_elapsed_sec > 0:
            throughput = successful_ops / total_elapsed_sec
        else:
            total_time_s = np.sum(latencies) / 1000.0
            throughput = successful_ops / max(0.001, total_time_s)
    else:
        p50 = p90 = p95 = p99 = mean = min_v = max_v = std = throughput = None

    return AggregatedResult(
        database=database,
        workload=workload,
        run_id=run_id,
        iterations=total_iterations,
        successful_operations=successful_ops,
        failed_operations=failed_ops,
        p50_ms=round(p50, 4) if p50 is not None else None,
        p90_ms=round(p90, 4) if p90 is not None else None,
        p95_ms=round(p95, 4) if p95 is not None else None,
        p99_ms=round(p99, 4) if p99 is not None else None,
        mean_ms=round(mean, 4) if mean is not None else None,
        min_ms=round(min_v, 4) if min_v is not None else None,
        max_ms=round(max_v, 4) if max_v is not None else None,
        stddev_ms=round(std, 4) if std is not None else None,
        throughput_ops_sec=round(throughput, 2) if throughput is not None else None,
        error_breakdown=error_breakdown
    )


class ResultStore:
    """Manages writing and reading raw JSONL and aggregated summaries."""

    def __init__(self, raw_dir: Path, processed_dir: Path):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def save_raw_results(
        self,
        database: str,
        run_id: str,
        workload: str,
        results: List[BenchmarkResult]
    ) -> Path:
        """Saves individual raw iteration records as JSONL."""
        db_raw_dir = self.raw_dir / database
        db_raw_dir.mkdir(parents=True, exist_ok=True)
        file_path = db_raw_dir / f"{workload}_{run_id}.jsonl"

        with open(file_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r.to_dict()) + "\n")

        logger.debug(f"Saved {len(results)} raw results to {file_path}")
        return file_path

    def save_aggregated_summary(
        self,
        results: List[AggregatedResult],
        append: bool = True
    ) -> Path:
        """Saves aggregated summary metrics to CSV and JSON."""
        csv_path = self.processed_dir / "aggregated_summary.csv"
        json_path = self.processed_dir / "aggregated_summary.json"

        records = [r.to_dict() for r in results]
        df_new = pd.DataFrame(records)

        if append and csv_path.exists():
            df_existing = pd.read_csv(csv_path)
            # Remove any identical (database, workload, run_id) duplicates before merging
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.drop_duplicates(subset=["database", "workload", "run_id"], keep="last", inplace=True)
        else:
            df_combined = df_new

        df_combined.to_csv(csv_path, index=False)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(df_combined.to_dict(orient="records"), f, indent=2)

        logger.info(f"Updated aggregated summary at {csv_path}")
        return csv_path

    def save_load_results(
        self,
        results: List[LoadResult],
        append: bool = True
    ) -> Path:
        """Saves data loading metrics to CSV and JSON."""
        csv_path = self.processed_dir / "load_summary.csv"
        records = [r.to_dict() for r in results]
        df_new = pd.DataFrame(records)

        if append and csv_path.exists():
            df_existing = pd.read_csv(csv_path)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.drop_duplicates(subset=["database", "run_id"], keep="last", inplace=True)
        else:
            df_combined = df_new

        df_combined.to_csv(csv_path, index=False)
        return csv_path

    def save_mixed_results(
        self,
        results: List[MixedWorkloadResult],
        append: bool = True
    ) -> Path:
        """Saves concurrency mixed workload metrics to CSV and JSON."""
        csv_path = self.processed_dir / "mixed_summary.csv"
        records = [r.to_dict() for r in results]
        df_new = pd.DataFrame(records)

        if append and csv_path.exists():
            df_existing = pd.read_csv(csv_path)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.drop_duplicates(subset=["database", "concurrency", "run_id"], keep="last", inplace=True)
        else:
            df_combined = df_new

        df_combined.to_csv(csv_path, index=False)
        return csv_path

    def save_resource_metrics(
        self,
        results: List[ResourceMetric]
    ) -> Path:
        """Saves observed resource snapshots."""
        csv_path = self.processed_dir / "resources_summary.csv"
        df = pd.DataFrame([r.to_dict() for r in results])
        df.to_csv(csv_path, index=False)
        return csv_path
