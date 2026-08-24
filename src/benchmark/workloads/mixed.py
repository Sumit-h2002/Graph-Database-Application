"""
Concurrent multi-client mixed read/write workload engine.
"""

from __future__ import annotations

import concurrent.futures
import logging
import random
import time
from typing import Any, Dict, List, Optional
import numpy as np

from benchmark.adapters.base import GraphDatabaseAdapter
from benchmark.models import MixedWorkloadResult

logger = logging.getLogger("benchmark.workloads.mixed")


class MixedReadWriteWorkload:
    """
    Simulates concurrent multi-client traffic with configurable read/write ratios.
    Evaluates database behavior under 10, 20, and 40 concurrent client connections.
    """

    def __init__(
        self,
        node_ids: List[int],
        categories: Optional[List[str]] = None,
        concurrency_levels: Optional[List[int]] = None,
        read_ratio: float = 0.8,
        write_ratio: float = 0.2,
        duration_seconds: float = 30.0,
        random_seed: int = 42,
    ):
        self.name = "mixed_read_write"
        self.node_ids = node_ids or [1]
        self.categories = categories or ["Astrophysics", "Quantum Physics", "String Theory"]
        self.concurrency_levels = concurrency_levels or [10, 20, 40]
        self.read_ratio = read_ratio
        self.write_ratio = write_ratio
        self.duration_seconds = duration_seconds
        self.random_seed = random_seed

    def run_level(
        self,
        adapter: GraphDatabaseAdapter,
        concurrency: int,
        run_id: str
    ) -> MixedWorkloadResult:
        """Runs the mixed benchmark for a single concurrency level."""
        logger.info(
            f"[{adapter.db_key}] Starting mixed read/write workload: concurrency={concurrency}, "
            f"duration={self.duration_seconds}s, read_ratio={self.read_ratio:.0%}, write_ratio={self.write_ratio:.0%}..."
        )

        stop_time = time.time() + self.duration_seconds
        latencies_ms: List[float] = []
        read_count = 0
        write_count = 0
        success_count = 0
        failed_count = 0
        error_breakdown: Dict[str, int] = {}

        synthetic_id_counter_base = 10_000_000 + concurrency * 100_000

        def worker_loop(worker_id: int) -> Dict[str, Any]:
            worker_rng = random.Random(self.random_seed + worker_id * 1000)
            w_latencies = []
            w_reads = 0
            w_writes = 0
            w_success = 0
            w_failed = 0
            w_errors: Dict[str, int] = {}
            op_idx = 0

            while time.time() < stop_time:
                op_idx += 1
                is_read = worker_rng.random() < self.read_ratio

                if is_read:
                    target_id = worker_rng.choice(self.node_ids)
                    query, params = adapter.translate_workload_query("mixed_read", {"node_id": target_id})
                    w_reads += 1
                else:
                    new_id = synthetic_id_counter_base + (worker_id * 10_000) + op_idx
                    cat = worker_rng.choice(self.categories)
                    year = worker_rng.randint(2020, 2026)
                    query, params = adapter.translate_workload_query("mixed_write", {
                        "new_id": new_id,
                        "name": f"SyntheticPaper_{new_id}",
                        "category": cat,
                        "year": year
                    })
                    w_writes += 1

                t_start = time.perf_counter_ns()
                try:
                    adapter.execute_query(query, params)
                    t_end = time.perf_counter_ns()
                    dur_ms = (t_end - t_start) / 1_000_000.0
                    w_latencies.append(dur_ms)
                    w_success += 1
                except Exception as e:
                    t_end = time.perf_counter_ns()
                    dur_ms = (t_end - t_start) / 1_000_000.0
                    w_latencies.append(dur_ms)
                    w_failed += 1
                    err_type = type(e).__name__
                    w_errors[err_type] = w_errors.get(err_type, 0) + 1

            return {
                "latencies": w_latencies,
                "reads": w_reads,
                "writes": w_writes,
                "success": w_success,
                "failed": w_failed,
                "errors": w_errors
            }

        # Execute concurrent worker threads
        start_benchmark = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(worker_loop, w_id) for w_id in range(concurrency)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    latencies_ms.extend(res["latencies"])
                    read_count += res["reads"]
                    write_count += res["writes"]
                    success_count += res["success"]
                    failed_count += res["failed"]
                    for err, count in res["errors"].items():
                        error_breakdown[err] = error_breakdown.get(err, 0) + count
                except Exception as e:
                    logger.error(f"Worker thread error: {e}")

        total_duration = max(0.001, time.perf_counter() - start_benchmark)
        total_ops = success_count + failed_count
        throughput = total_ops / total_duration
        read_throughput = read_count / total_duration
        write_throughput = write_count / total_duration
        error_rate = (failed_count / total_ops) if total_ops > 0 else 0.0

        p50 = float(np.percentile(latencies_ms, 50)) if latencies_ms else None
        p95 = float(np.percentile(latencies_ms, 95)) if latencies_ms else None
        p99 = float(np.percentile(latencies_ms, 99)) if latencies_ms else None

        logger.info(
            f"[{adapter.db_key}] Concurrency={concurrency} finished: {total_ops:,} ops in {total_duration:.2f}s "
            f"({throughput:.1f} ops/s, p50={p50:.2f}ms, p95={p95:.2f}ms, errors={failed_count})"
        )

        return MixedWorkloadResult(
            database=adapter.db_key,
            run_id=run_id,
            concurrency=concurrency,
            duration_seconds=round(total_duration, 2),
            total_operations=total_ops,
            successful_operations=success_count,
            failed_operations=failed_count,
            throughput_ops_sec=round(throughput, 2),
            read_operations=read_count,
            write_operations=write_count,
            read_throughput_ops_sec=round(read_throughput, 2),
            write_throughput_ops_sec=round(write_throughput, 2),
            p50_ms=round(p50, 4) if p50 is not None else None,
            p95_ms=round(p95, 4) if p95 is not None else None,
            p99_ms=round(p99, 4) if p99 is not None else None,
            error_rate=round(error_rate, 4),
            error_breakdown=error_breakdown
        )
