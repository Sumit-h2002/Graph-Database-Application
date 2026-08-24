"""
Data loading benchmark workload.
"""

from __future__ import annotations

import logging
from typing import Optional
import pandas as pd

from benchmark.adapters.base import GraphDatabaseAdapter
from benchmark.models import LoadResult

logger = logging.getLogger("benchmark.workloads.loading")


class LoadingWorkload:
    """Measures data ingestion latency and throughput across databases."""

    def __init__(self, batch_size: int = 5000):
        self.name = "loading"
        self.batch_size = batch_size

    def run(
        self,
        adapter: GraphDatabaseAdapter,
        nodes_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        run_id: str = "run_1"
    ) -> LoadResult:
        """Executes full database load and returns measured LoadResult."""
        logger.info(
            f"[{adapter.db_key}] Executing Loading Workload: {len(nodes_df):,} nodes, "
            f"{len(edges_df):,} edges, batch_size={self.batch_size}..."
        )
        return adapter.load_data(nodes_df, edges_df, batch_size=self.batch_size, run_id=run_id)
