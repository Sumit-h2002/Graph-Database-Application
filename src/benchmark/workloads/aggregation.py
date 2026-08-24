"""
Aggregation workload measuring grouped analytical aggregations.
"""

from __future__ import annotations

from typing import Any, Dict
from benchmark.workloads.base import BaseWorkload


class AggregationWorkload(BaseWorkload):
    """Measures grouped analytical aggregation (e.g. relationship count grouped by category)."""

    def __init__(
        self,
        warmup_iterations: int = 20,
        measurement_iterations: int = 100,
        timeout_seconds: float = 60.0
    ):
        super().__init__(
            name="aggregation",
            warmup_iterations=warmup_iterations,
            measurement_iterations=measurement_iterations,
            timeout_seconds=timeout_seconds
        )

    def generate_params(self, iteration: int, is_warmup: bool) -> Dict[str, Any]:
        return {}
