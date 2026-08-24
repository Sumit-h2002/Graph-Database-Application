"""
FalkorDB Database Adapter using FalkorDB / Redis Graph Python Driver.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from benchmark.adapters.base import GraphDatabaseAdapter
from benchmark.models import DatabaseMetadata, LoadResult

logger = logging.getLogger("benchmark.adapters.falkordb")


class FalkorDBAdapter(GraphDatabaseAdapter):
    """
    Adapter for FalkorDB graph database via Redis / FalkorDB protocol.
    """

    def __init__(self, metadata: DatabaseMetadata):
        super().__init__("falkordb", metadata)
        self.uri = os.getenv("FALKORDB_URI", "")
        self.host = os.getenv("FALKORDB_HOST", "")
        self.port = int(os.getenv("FALKORDB_PORT", "6379")) if os.getenv("FALKORDB_PORT") else 6379
        self.username = os.getenv("FALKORDB_USERNAME", "")
        self.password = os.getenv("FALKORDB_PASSWORD", "") or None
        self.graph_name = os.getenv("FALKORDB_GRAPH_NAME", "benchmark_graph")
        self._client = None
        self._graph = None

    def connect(self) -> None:
        if not self.uri and not self.host:
            raise ValueError("Missing required environment variable: FALKORDB_URI (or FALKORDB_HOST)")

        try:
            try:
                from falkordb import FalkorDB
                if self.uri:
                    self._client = FalkorDB.from_url(self.uri)
                else:
                    self._client = FalkorDB(
                        host=self.host,
                        port=self.port,
                        username=self.username or None,
                        password=self.password
                    )
                self._graph = self._client.select_graph(self.graph_name)
            except (ImportError, AttributeError):
                import redis
                if self.uri:
                    r = redis.from_url(self.uri, decode_responses=True)
                else:
                    r = redis.Redis(
                        host=self.host,
                        port=self.port,
                        username=self.username or None,
                        password=self.password,
                        decode_responses=True
                    )
                self._client = r
                self._graph = r.graph(self.graph_name)

            # Test connection
            self._graph.query("RETURN 1 AS ping")
            self.is_connected = True
            logger.info("Connected successfully to FalkorDB endpoint.")
        except Exception as e:
            self.is_connected = False
            logger.error(f"Failed to connect to FalkorDB: {e}")
            raise

    def close(self) -> None:
        if self._client:
            try:
                if hasattr(self._client, "close"):
                    self._client.close()
            except Exception:
                pass
            self.is_connected = False
            logger.info("Closed FalkorDB connection.")

    def health_check(self) -> bool:
        if not self._graph:
            return False
        try:
            res = self._graph.query("RETURN 1 AS ping")
            return res is not None
        except Exception as e:
            logger.warning(f"FalkorDB health check failed: {e}")
            return False

    def clear_database(self) -> None:
        logger.info(f"Clearing FalkorDB graph '{self.graph_name}'...")
        try:
            self._graph.delete()
        except Exception as e:
            logger.warning(f"FalkorDB graph delete notice: {e}. Executing MATCH (n) DETACH DELETE n...")
            try:
                self._graph.query("MATCH (n) DETACH DELETE n")
            except Exception:
                pass
        logger.info("FalkorDB cleared.")

    def create_schema(self) -> None:
        logger.info("Creating FalkorDB property indexes...")
        try:
            self._graph.query("CREATE INDEX FOR (p:Paper) ON (p.id)")
        except Exception as e:
            logger.warning(f"FalkorDB Paper.id index notice: {e}")

        try:
            self._graph.query("CREATE INDEX FOR (p:Paper) ON (p.category)")
        except Exception as e:
            logger.warning(f"FalkorDB Paper.category index notice: {e}")
        logger.info("FalkorDB schema configured.")

    def load_data(
        self,
        nodes_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        batch_size: int = 5000,
        run_id: str = "init"
    ) -> LoadResult:
        logger.info(f"Starting FalkorDB data loading ({len(nodes_df)} nodes, {len(edges_df)} edges, batch_size={batch_size})...")
        start_total = time.perf_counter()

        # 1. Ingest Nodes
        start_nodes = time.perf_counter()
        node_records = nodes_df.to_dict(orient="records")
        node_query = """
        UNWIND $batch AS row
        CREATE (p:Paper {
            id: row.id,
            name: row.name,
            category: row.category,
            year: row.year,
            weight: row.weight
        })
        """
        for i in range(0, len(node_records), batch_size):
            batch = node_records[i : i + batch_size]
            self._graph.query(node_query, {"batch": batch})
        node_load_time = time.perf_counter() - start_nodes

        # 2. Ingest Edges
        start_edges = time.perf_counter()
        edge_records = edges_df.to_dict(orient="records")
        edge_query = """
        UNWIND $batch AS row
        MATCH (src:Paper {id: row.source_id})
        MATCH (dst:Paper {id: row.target_id})
        CREATE (src)-[:CITES {weight: row.weight}]->(dst)
        """
        for i in range(0, len(edge_records), batch_size):
            batch = edge_records[i : i + batch_size]
            self._graph.query(edge_query, {"batch": batch})
        rel_load_time = time.perf_counter() - start_edges

        total_load_time = time.perf_counter() - start_total
        total_records = len(nodes_df) + len(edges_df)

        nodes_per_sec = len(nodes_df) / max(0.001, node_load_time)
        rels_per_sec = len(edges_df) / max(0.001, rel_load_time)
        total_records_per_sec = total_records / max(0.001, total_load_time)

        logger.info(
            f"FalkorDB loading complete: {len(nodes_df)} nodes in {node_load_time:.2f}s ({nodes_per_sec:.1f} nodes/s), "
            f"{len(edges_df)} rels in {rel_load_time:.2f}s ({rels_per_sec:.1f} rels/s)."
        )

        return LoadResult(
            database=self.db_key,
            run_id=run_id,
            nodes_loaded=len(nodes_df),
            rels_loaded=len(edges_df),
            total_records=total_records,
            node_load_time_sec=round(node_load_time, 4),
            rel_load_time_sec=round(rel_load_time, 4),
            total_load_time_sec=round(total_load_time, 4),
            nodes_per_sec=round(nodes_per_sec, 2),
            rels_per_sec=round(rels_per_sec, 2),
            total_records_per_sec=round(total_records_per_sec, 2),
            batch_size=batch_size,
            success=True
        )

    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        params = params or {}
        res = self._graph.query(query, params)
        return res.result_set if hasattr(res, "result_set") else res
