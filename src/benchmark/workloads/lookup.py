"""
Point lookup and filtered property lookup workloads.
"""

from __future__ import annotations

from typing import Any, Dict, List
from benchmark.workloads.base import BaseWorkload


class PointLookupWorkload(BaseWorkload):
    """Measures indexed primary key lookup latency for single nodes."""

    def __init__(
        self,
        node_ids: List[int],
        warmup_iterations: int = 20,
        measurement_iterations: int = 100,
        timeout_seconds: float = 60.0
    ):
        super().__init__(
            name="point_lookup",
            warmup_iterations=warmup_iterations,
            measurement_iterations=measurement_iterations,
            timeout_seconds=timeout_seconds
        )
        self.node_ids = node_ids or [1]

    def generate_params(self, iteration: int, is_warmup: bool) -> Dict[str, Any]:
        node_id = self.node_ids[iteration % len(self.node_ids)]
        return {"node_id": node_id}


class FilteredLookupWorkload(BaseWorkload):
    """Measures property-filtered node search across categories."""

    def __init__(
        self,
        categories: List[str],
        warmup_iterations: int = 20,
        measurement_iterations: int = 100,
        timeout_seconds: float = 60.0
    ):
        super().__init__(
            name="filtered_lookup",
            warmup_iterations=warmup_iterations,
            measurement_iterations=measurement_iterations,
            timeout_seconds=timeout_seconds
        )
        self.categories = categories or ["Astrophysics", "Quantum Physics", "String Theory"]

    def generate_params(self, iteration: int, is_warmup: bool) -> Dict[str, Any]:
        cat = self.categories[iteration % len(self.categories)]
        return {"category": cat}
