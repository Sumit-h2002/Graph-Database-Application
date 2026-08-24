"""
Abstract base class and contract for all graph database adapters.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import psutil

from benchmark.models import DatabaseMetadata, LoadResult, ResourceMetric

logger = logging.getLogger("benchmark.adapters.base")


class GraphDatabaseAdapter(ABC):
    """
    Unified abstract database adapter interface.
    All benchmark runner operations interact exclusively through this abstraction.
    """

    def __init__(self, db_key: str, metadata: DatabaseMetadata):
        self.db_key = db_key
        self.metadata = metadata
        self.is_connected = False

    @abstractmethod
    def connect(self) -> None:
        """Establishes connection to the target database."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Closes all active database connections and client sessions."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Performs a lightweight ping or read query to verify connectivity."""
        pass

    @abstractmethod
    def clear_database(self) -> None:
        """Deletes all nodes, relationships, and custom schema from the graph."""
        pass

    @abstractmethod
    def create_schema(self) -> None:
        """Creates unique constraints and property indexes (e.g. on Paper.id and Paper.category)."""
        pass

    @abstractmethod
    def load_data(
        self,
        nodes_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        batch_size: int = 5000,
        run_id: str = "init"
    ) -> LoadResult:
        """
        Loads nodes and relationships into the database using the platform's
        most efficient supported batched mechanism.
        """
        pass

    @abstractmethod
    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Executes a single query and returns results."""
        pass

    def translate_workload_query(
        self,
        workload_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Translates a logical workload name into the database-specific query syntax
        and parameter payload. Default implementation uses standard Cypher.
        """
        params = params or {}

        if workload_name == "traversal_1_hop":
            query = "MATCH (n:Paper {id: $node_id})-[r:CITES]->(m:Paper) RETURN count(m) AS neighbor_count"
        elif workload_name == "traversal_2_hop":
            query = "MATCH (n:Paper {id: $node_id})-[r1:CITES]->(m:Paper)-[r2:CITES]->(k:Paper) RETURN count(DISTINCT k) AS two_hop_count"
        elif workload_name == "traversal_3_hop":
            query = "MATCH (n:Paper {id: $node_id})-[r1:CITES]->(m:Paper)-[r2:CITES]->(k:Paper)-[r3:CITES]->(p:Paper) RETURN count(DISTINCT p) AS three_hop_count"
        elif workload_name == "point_lookup":
            query = "MATCH (n:Paper {id: $node_id}) RETURN n.id AS id, n.name AS name, n.category AS category, n.year AS year"
        elif workload_name == "filtered_lookup":
            query = "MATCH (n:Paper) WHERE n.category = $category RETURN count(n) AS match_count"
        elif workload_name == "aggregation":
            query = "MATCH (n:Paper)-[r:CITES]->(m:Paper) RETURN n.category AS category, count(r) AS citation_count ORDER BY citation_count DESC LIMIT 20"
        elif workload_name == "mixed_read":
            query = "MATCH (n:Paper {id: $node_id})-[r:CITES]->(m:Paper) RETURN count(m) AS neighbor_count"
        elif workload_name == "mixed_write":
            query = "CREATE (n:Paper {id: $new_id, name: $name, category: $category, year: $year, is_synthetic: true})"
        else:
            raise ValueError(f"Unknown workload: {workload_name}")

        return query, params

    def get_resource_usage(self) -> ResourceMetric:
        """
        Gathers observable hardware metrics if running locally or via self-hosted process.
        Remote cloud instances return is_observable=False with documented limits.
        """
        if self.metadata.hosting == "cloud":
            return ResourceMetric(
                database=self.db_key,
                cpu_percent=None,
                memory_used_mb=None,
                memory_total_mb=self.metadata.ram_gb * 1024,
                database_size_mb=None,
                is_observable=False,
                notes=f"Remote cloud DBaaS ({self.metadata.region}). Cloud host metrics are not exposed via client driver."
            )

        try:
            vm = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.05)
            return ResourceMetric(
                database=self.db_key,
                cpu_percent=cpu,
                memory_used_mb=round((vm.total - vm.available) / (1024 * 1024), 2),
                memory_total_mb=round(vm.total / (1024 * 1024), 2),
                database_size_mb=None,
                is_observable=True,
                notes="Host client-side observable resource snapshot"
            )
        except Exception as e:
            return ResourceMetric(
                database=self.db_key,
                is_observable=False,
                notes=f"Resource collection error: {e}"
            )
