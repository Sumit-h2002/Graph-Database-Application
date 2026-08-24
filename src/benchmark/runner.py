"""
Core benchmark runner coordinating datasets, workloads, adapters, timing, and storage.
"""

from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from benchmark.adapters import get_adapter
from benchmark.adapters.base import GraphDatabaseAdapter
from benchmark.config import BenchmarkConfig
from benchmark.models import (
    AggregatedResult,
    BenchmarkResult,
    DatabaseMetadata,
    LoadResult,
    MixedWorkloadResult,
    ResourceMetric,
)
from benchmark.statistics import ResultStore, calculate_aggregated_result
from benchmark.workloads import (
    AggregationWorkload,
    FilteredLookupWorkload,
    LoadingWorkload,
    MixedReadWriteWorkload,
    PointLookupWorkload,
    Traversal1HopWorkload,
    Traversal2HopWorkload,
    Traversal3HopWorkload,
)

logger = logging.getLogger("benchmark.runner")


class BenchmarkRunner:
    """Orchestrates benchmark workflows against target graph database platforms."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.result_store = ResultStore(
            raw_dir=config.raw_results_dir,
            processed_dir=config.processed_results_dir
        )
        self.rng = random.Random(config.random_seed)

    def load_dataset(self) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Loads normalized processed dataset CSVs."""
        nodes_path = self.config.processed_data_dir / "nodes.csv"
        edges_path = self.config.processed_data_dir / "edges.csv"

        if not nodes_path.exists() or not edges_path.exists():
            raise FileNotFoundError(
                f"Processed dataset not found at {self.config.processed_data_dir}. "
                "Please run 'python -m benchmark.cli prepare-data' first."
            )

        logger.info(f"Loading processed dataset from {self.config.processed_data_dir}...")
        nodes_df = pd.read_csv(nodes_path)
        edges_df = pd.read_csv(edges_path)
        return nodes_df, edges_df, {}

    def get_deterministic_sample_nodes(self, nodes_df: pd.DataFrame, count: int = 500) -> List[int]:
        """Samples deterministic node IDs using fixed seed for reproducible traversals/lookups."""
        all_ids = sorted(nodes_df["id"].tolist())
        self.rng.seed(self.config.random_seed)
        sampled = self.rng.sample(all_ids, min(count, len(all_ids)))
        return sampled

    def run_database_benchmark(
        self,
        db_key: str,
        adapter_override: Optional[GraphDatabaseAdapter] = None,
        skip_load: bool = False
    ) -> Dict[str, Any]:
        """Executes full benchmark suite against a single database."""
        db_meta = self.config.get_database_config(db_key)
        if not db_meta and adapter_override and hasattr(adapter_override, "metadata"):
            db_meta = adapter_override.metadata
        elif not db_meta:
            raise ValueError(f"Database configuration not found for '{db_key}'")

        adapter = adapter_override or get_adapter(db_key, db_meta)

        logger.info(f"============================================================")
        logger.info(f"Starting Benchmark for: {db_meta.name} ({db_key})")
        logger.info(f"============================================================")

        nodes_df, edges_df, _ = self.load_dataset()
        categories = sorted(list(nodes_df["category"].unique()))
        sample_node_ids = self.get_deterministic_sample_nodes(nodes_df, count=500)

        load_results: List[LoadResult] = []
        aggregated_results: List[AggregatedResult] = []
        mixed_results: List[MixedWorkloadResult] = []
        resource_metrics: List[ResourceMetric] = []

        try:
            adapter.connect()
            if not adapter.health_check():
                raise ConnectionError(f"Health check failed for database '{db_key}'")

            # Initial resource measurement
            res_before = adapter.get_resource_usage()
            resource_metrics.append(res_before)

            # Repetitions
            for rep in range(1, self.config.repetitions + 1):
                run_id = f"run_{rep}_{int(time.time())}"
                logger.info(f"--- Repetition {rep}/{self.config.repetitions} (Run ID: {run_id}) ---")

                # Phase A: Clear, Schema & Loading (Only on rep 1 or full test)
                if rep == 1 and not skip_load:
                    adapter.clear_database()
                    adapter.create_schema()

                    loader = LoadingWorkload(batch_size=self.config.default_batch_size)
                    load_res = loader.run(adapter, nodes_df, edges_df, run_id=run_id)
                    load_results.append(load_res)

                # Instantiate standard read workloads
                workloads = [
                    PointLookupWorkload(
                        node_ids=sample_node_ids,
                        warmup_iterations=self.config.warmup_iterations,
                        measurement_iterations=self.config.measurement_iterations,
                        timeout_seconds=self.config.timeout_seconds
                    ),
                    FilteredLookupWorkload(
                        categories=categories,
                        warmup_iterations=self.config.warmup_iterations,
                        measurement_iterations=self.config.measurement_iterations,
                        timeout_seconds=self.config.timeout_seconds
                    ),
                    Traversal1HopWorkload(
                        start_node_ids=sample_node_ids,
                        warmup_iterations=self.config.warmup_iterations,
                        measurement_iterations=self.config.measurement_iterations,
                        timeout_seconds=self.config.timeout_seconds
                    ),
                    Traversal2HopWorkload(
                        start_node_ids=sample_node_ids,
                        warmup_iterations=self.config.warmup_iterations,
                        measurement_iterations=self.config.measurement_iterations,
                        timeout_seconds=self.config.timeout_seconds
                    ),
                    Traversal3HopWorkload(
                        start_node_ids=sample_node_ids,
                        warmup_iterations=self.config.warmup_iterations,
                        measurement_iterations=self.config.measurement_iterations,
                        timeout_seconds=self.config.timeout_seconds
                    ),
                    AggregationWorkload(
                        warmup_iterations=self.config.warmup_iterations,
                        measurement_iterations=self.config.measurement_iterations,
                        timeout_seconds=self.config.timeout_seconds
                    ),
                ]

                for wl in workloads:
                    # 1. Warm-up
                    wl.run_warmup(adapter)

                    # 2. Measurement
                    t0 = time.perf_counter()
                    raw_items = wl.run_measurement(adapter, run_id=run_id)
                    t_elapsed = time.perf_counter() - t0

                    # 3. Store raw iteration records
                    self.result_store.save_raw_results(db_key, run_id, wl.name, raw_items)

                    # 4. Compute statistics
                    agg = calculate_aggregated_result(raw_items, total_elapsed_sec=t_elapsed)
                    aggregated_results.append(agg)

                # Mixed Concurrency Workload (on last repetition to avoid mutating graph mid-traversal)
                if rep == self.config.repetitions:
                    mixed_cfg = self.config.get_mixed_workload_config()
                    mixed_wl = MixedReadWriteWorkload(
                        node_ids=sample_node_ids,
                        categories=categories,
                        concurrency_levels=mixed_cfg.get("concurrency_levels", [10, 20, 40]),
                        read_ratio=float(mixed_cfg.get("read_ratio", 0.8)),
                        write_ratio=float(mixed_cfg.get("write_ratio", 0.2)),
                        duration_seconds=float(mixed_cfg.get("duration_seconds", 30.0)),
                        random_seed=self.config.random_seed
                    )
                    for conc in mixed_wl.concurrency_levels:
                        m_res = mixed_wl.run_level(adapter, concurrency=conc, run_id=run_id)
                        mixed_results.append(m_res)

            # Post-benchmark resource snapshot
            res_after = adapter.get_resource_usage()
            resource_metrics.append(res_after)

            # Persist processed summaries
            if load_results:
                self.result_store.save_load_results(load_results)
            if aggregated_results:
                self.result_store.save_aggregated_summary(aggregated_results)
            if mixed_results:
                self.result_store.save_mixed_results(mixed_results)
            if resource_metrics:
                self.result_store.save_resource_metrics(resource_metrics)

            logger.info(f"Benchmark completed successfully for {db_key}.")

        finally:
            adapter.close()

        return {
            "database": db_key,
            "load_results": load_results,
            "aggregated_results": aggregated_results,
            "mixed_results": mixed_results,
            "resource_metrics": resource_metrics
        }
