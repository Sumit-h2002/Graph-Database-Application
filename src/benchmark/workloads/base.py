"""
Base workload class with nanosecond precision measurement and warm-up isolation.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from benchmark.adapters.base import GraphDatabaseAdapter
from benchmark.models import BenchmarkResult

logger = logging.getLogger("benchmark.workloads.base")


class BaseWorkload(ABC):
    """
    Abstract workload class handling warm-up execution, measurement execution,
    and nanosecond precision timing.
    """

    def __init__(
        self,
        name: str,
        warmup_iterations: int = 20,
        measurement_iterations: int = 100,
        timeout_seconds: float = 60.0,
    ):
        self.name = name
        self.warmup_iterations = warmup_iterations
        self.measurement_iterations = measurement_iterations
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def generate_params(self, iteration: int, is_warmup: bool) -> Dict[str, Any]:
        """Generates query parameters for a specific iteration."""
        pass

    def run_warmup(self, adapter: GraphDatabaseAdapter) -> int:
        """Executes unmeasured warm-up iterations to prime database caches and connections."""
        logger.info(f"[{adapter.db_key}] Warming up '{self.name}' ({self.warmup_iterations} iterations)...")
        completed = 0
        for i in range(self.warmup_iterations):
            params = self.generate_params(i, is_warmup=True)
            query, translated_params = adapter.translate_workload_query(self.name, params)
            try:
                adapter.execute_query(query, translated_params)
                completed += 1
            except Exception as e:
                logger.debug(f"Warm-up iteration {i} notice: {e}")
        return completed

    def run_measurement(
        self,
        adapter: GraphDatabaseAdapter,
        run_id: str
    ) -> List[BenchmarkResult]:
        """
        Executes measured iterations using time.perf_counter_ns()
        and captures fine-grained success, latency, and error states.
        """
        results: List[BenchmarkResult] = []
        logger.info(f"[{adapter.db_key}] Executing '{self.name}' ({self.measurement_iterations} measured iterations)...")

        for i in range(self.measurement_iterations):
            params = self.generate_params(i, is_warmup=False)
            query, translated_params = adapter.translate_workload_query(self.name, params)

            start_ns = time.perf_counter_ns()
            success = False
            error_type = None
            error_msg = None
            latency_ns = None
            latency_ms = None

            try:
                adapter.execute_query(query, translated_params)
                end_ns = time.perf_counter_ns()
                latency_ns = end_ns - start_ns
                latency_ms = latency_ns / 1_000_000.0
                success = True
            except TimeoutError as e:
                end_ns = time.perf_counter_ns()
                latency_ns = end_ns - start_ns
                latency_ms = latency_ns / 1_000_000.0
                error_type = "timeout"
                error_msg = str(e)
                logger.warning(f"[{adapter.db_key}] Query timeout on iteration {i}: {e}")
            except ConnectionError as e:
                error_type = "connection_error"
                error_msg = str(e)
                logger.error(f"[{adapter.db_key}] Connection lost on iteration {i}: {e}")
            except Exception as e:
                end_ns = time.perf_counter_ns()
                latency_ns = end_ns - start_ns
                latency_ms = latency_ns / 1_000_000.0
                error_type = type(e).__name__
                error_msg = str(e)
                logger.warning(f"[{adapter.db_key}] Query failed on iteration {i}: {e}")

            results.append(BenchmarkResult(
                database=adapter.db_key,
                workload=self.name,
                run_id=run_id,
                iteration=i + 1,
                latency_ms=round(latency_ms, 4) if latency_ms is not None else None,
                latency_ns=latency_ns,
                success=success,
                error_type=error_type,
                error_message=error_msg,
                params_summary=str(params)
            ))

        return results
