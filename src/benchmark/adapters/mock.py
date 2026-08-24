"""
Mock Database Adapter for unit testing, offline dry-runs, and contract validation.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
import pandas as pd

from benchmark.adapters.base import GraphDatabaseAdapter
from benchmark.models import DatabaseMetadata, LoadResult, ResourceMetric

logger = logging.getLogger("benchmark.adapters.mock")


class MockDatabaseAdapter(GraphDatabaseAdapter):
    """
    In-memory mock adapter simulating a graph database.
    Used for unit testing, CI pipelines, and offline verification.
    """

    def __init__(self, db_key: str = "mock_db", metadata: Optional[DatabaseMetadata] = None):
        meta = metadata or DatabaseMetadata(
            name="Mock Database",
            key=db_key,
            version="1.0.0-mock",
            deployment_type="In-Memory Mock",
            hosting="local",
            region="local",
            vcpu=2,
            ram_gb=4.0,
            storage_gb=20.0,
            resource_limitations="None (Mock)",
            driver="internal-mock",
            query_language="Cypher (Simulated)",
            indexing_support="In-memory hash index",
            import_method="Direct memory append",
            enabled=True
        )
        super().__init__(db_key, meta)
        self.nodes = {}
        self.edges = []
        self.schema_created = False

    def connect(self) -> None:
        self.is_connected = True
        logger.info(f"Connected to {self.db_key} mock adapter.")

    def close(self) -> None:
        self.is_connected = False
        logger.info(f"Closed {self.db_key} mock adapter.")

    def health_check(self) -> bool:
        return self.is_connected

    def clear_database(self) -> None:
        self.nodes.clear()
        self.edges.clear()
        self.schema_created = False
        logger.info(f"Cleared {self.db_key} mock adapter data.")

    def create_schema(self) -> None:
        self.schema_created = True
        logger.info(f"Created schema on {self.db_key} mock adapter.")

    def load_data(
        self,
        nodes_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        batch_size: int = 5000,
        run_id: str = "init"
    ) -> LoadResult:
        start_total = time.perf_counter()
        for _, row in nodes_df.iterrows():
            self.nodes[row["id"]] = row.to_dict()
        node_time = max(0.0001, time.perf_counter() - start_total)

        start_edges = time.perf_counter()
        for _, row in edges_df.iterrows():
            self.edges.append(row.to_dict())
        edge_time = max(0.0001, time.perf_counter() - start_edges)

        total_time = max(0.0001, time.perf_counter() - start_total)
        total_records = len(nodes_df) + len(edges_df)

        return LoadResult(
            database=self.db_key,
            run_id=run_id,
            nodes_loaded=len(nodes_df),
            rels_loaded=len(edges_df),
            total_records=total_records,
            node_load_time_sec=round(node_time, 4),
            rel_load_time_sec=round(edge_time, 4),
            total_load_time_sec=round(total_time, 4),
            nodes_per_sec=round(len(nodes_df) / node_time, 2),
            rels_per_sec=round(len(edges_df) / edge_time, 2),
            total_records_per_sec=round(total_records / total_time, 2),
            batch_size=batch_size,
            success=True
        )

    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        params = params or {}
        # Minimal simulated response
        if "node_id" in params:
            node_id = params["node_id"]
            if node_id in self.nodes:
                return [{"id": node_id, "name": self.nodes[node_id].get("name", "Paper")}]
            return []
        if "category" in params:
            return [{"match_count": 42}]
        if "neighbor_count" in query:
            return [{"neighbor_count": 5}]
        return [{"count": 1}]

    def get_resource_usage(self) -> ResourceMetric:
        return ResourceMetric(
            database=self.db_key,
            cpu_percent=10.0,
            memory_used_mb=128.0,
            memory_total_mb=4096.0,
            is_observable=True,
            notes="Mock observable resource metrics"
        )
