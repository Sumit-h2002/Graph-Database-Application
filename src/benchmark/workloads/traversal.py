"""
1-hop, 2-hop, and 3-hop graph traversal workloads.
"""

from __future__ import annotations

from typing import Any, Dict, List
from benchmark.workloads.base import BaseWorkload


class Traversal1HopWorkload(BaseWorkload):
    """Measures 1-hop direct neighbor expansion from deterministic seed nodes."""

    def __init__(
        self,
        start_node_ids: List[int],
        warmup_iterations: int = 20,
        measurement_iterations: int = 100,
        timeout_seconds: float = 60.0
    ):
        super().__init__(
            name="traversal_1_hop",
            warmup_iterations=warmup_iterations,
            measurement_iterations=measurement_iterations,
            timeout_seconds=timeout_seconds
        )
        self.start_node_ids = start_node_ids or [1]

    def generate_params(self, iteration: int, is_warmup: bool) -> Dict[str, Any]:
        node_id = self.start_node_ids[iteration % len(self.start_node_ids)]
        return {"node_id": node_id}


class Traversal2HopWorkload(BaseWorkload):
    """Measures 2-hop neighborhood expansion from deterministic seed nodes."""

    def __init__(
        self,
        start_node_ids: List[int],
        warmup_iterations: int = 20,
        measurement_iterations: int = 100,
        timeout_seconds: float = 60.0
    ):
        super().__init__(
            name="traversal_2_hop",
            warmup_iterations=warmup_iterations,
            measurement_iterations=measurement_iterations,
            timeout_seconds=timeout_seconds
        )
        self.start_node_ids = start_node_ids or [1]

    def generate_params(self, iteration: int, is_warmup: bool) -> Dict[str, Any]:
        node_id = self.start_node_ids[iteration % len(self.start_node_ids)]
        return {"node_id": node_id}


class Traversal3HopWorkload(BaseWorkload):
    """Measures 3-hop deep path traversal from deterministic seed nodes."""

    def __init__(
        self,
        start_node_ids: List[int],
        warmup_iterations: int = 20,
        measurement_iterations: int = 100,
        timeout_seconds: float = 60.0
    ):
        super().__init__(
            name="traversal_3_hop",
            warmup_iterations=warmup_iterations,
            measurement_iterations=measurement_iterations,
            timeout_seconds=timeout_seconds
        )
        self.start_node_ids = start_node_ids or [1]

    def generate_params(self, iteration: int, is_warmup: bool) -> Dict[str, Any]:
        node_id = self.start_node_ids[iteration % len(self.start_node_ids)]
        return {"node_id": node_id}
