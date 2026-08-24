"""
Kùzu Graph Database Adapter using official Kùzu Python Driver.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from benchmark.adapters.base import GraphDatabaseAdapter
from benchmark.models import DatabaseMetadata, LoadResult

logger = logging.getLogger("benchmark.adapters.kuzu")


class KuzuAdapter(GraphDatabaseAdapter):
    """
    Adapter for Kùzu columnar disk-based graph database engine.
    """

    def __init__(self, metadata: DatabaseMetadata):
        super().__init__("kuzu", metadata)
        self.db_path = os.getenv("KUZU_DATABASE_PATH", "data/kuzu_db")
        self.buffer_pool_size_gb = float(os.getenv("KUZU_BUFFER_POOL_SIZE_GB", 1.0))
        self._db = None
        self._conn = None

    def connect(self) -> None:
        try:
            import kuzu
            buffer_pool_bytes = int(self.buffer_pool_size_gb * 1024 * 1024 * 1024)
            db_dir = Path(self.db_path)
            db_dir.parent.mkdir(parents=True, exist_ok=True)

            self._db = kuzu.Database(str(db_dir), buffer_pool_size=buffer_pool_bytes)
            self._conn = kuzu.Connection(self._db)
            self.is_connected = True
            logger.info(f"Connected successfully to Kùzu at {self.db_path}")
        except Exception as e:
            self.is_connected = False
            logger.error(f"Failed to connect to Kùzu at {self.db_path}: {e}")
            raise

    def close(self) -> None:
        self._conn = None
        self._db = None
        self.is_connected = False
        logger.info("Closed Kùzu connection.")

    def health_check(self) -> bool:
        if not self._conn:
            return False
        try:
            res = self._conn.execute("RETURN 1 AS ping")
            return res.has_next()
        except Exception as e:
            logger.warning(f"Kùzu health check failed: {e}")
            return False

    def clear_database(self) -> None:
        logger.info("Clearing Kùzu graph tables...")
        if self._conn:
            try:
                self._conn.execute("DROP TABLE CITES")
            except Exception:
                pass
            try:
                self._conn.execute("DROP TABLE Paper")
            except Exception:
                pass
        else:
            # If not connected, remove directory
            db_dir = Path(self.db_path)
            if db_dir.exists():
                shutil.rmtree(db_dir, ignore_errors=True)
        logger.info("Kùzu cleared.")

    def create_schema(self) -> None:
        logger.info("Creating Kùzu node and relationship schemas...")
        try:
            self._conn.execute(
                "CREATE NODE TABLE Paper(id INT64, name STRING, category STRING, year INT64, weight DOUBLE, PRIMARY KEY (id))"
            )
        except Exception as e:
            logger.warning(f"Kùzu Paper table creation notice: {e}")

        try:
            self._conn.execute(
                "CREATE REL TABLE CITES(FROM Paper TO Paper, weight DOUBLE)"
            )
        except Exception as e:
            logger.warning(f"Kùzu CITES table creation notice: {e}")

        logger.info("Kùzu schema configured.")

    def load_data(
        self,
        nodes_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        batch_size: int = 5000,
        run_id: str = "init"
    ) -> LoadResult:
        logger.info(f"Starting Kùzu data loading ({len(nodes_df)} nodes, {len(edges_df)} edges)...")
        start_total = time.perf_counter()

        # Ingest using temporary CSV files with native high-performance COPY FROM
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            tmp_nodes_csv = tmp_path / "nodes_kuzu.csv"
            tmp_edges_csv = tmp_path / "edges_kuzu.csv"

            # Reorder columns for clean COPY
            nodes_clean = nodes_df[["id", "name", "category", "year", "weight"]].copy()
            edges_clean = edges_df[["source_id", "target_id", "weight"]].copy()

            nodes_clean.to_csv(tmp_nodes_csv, index=False)
            edges_clean.to_csv(tmp_edges_csv, index=False)

            # Ingest Nodes
            start_nodes = time.perf_counter()
            formatted_nodes_path = str(tmp_nodes_csv).replace("\\", "/")
            self._conn.execute(f"COPY Paper FROM '{formatted_nodes_path}' (HEADER=true)")
            node_load_time = time.perf_counter() - start_nodes

            # Ingest Edges
            start_edges = time.perf_counter()
            formatted_edges_path = str(tmp_edges_csv).replace("\\", "/")
            self._conn.execute(f"COPY CITES FROM '{formatted_edges_path}' (HEADER=true)")
            rel_load_time = time.perf_counter() - start_edges

        total_load_time = time.perf_counter() - start_total
        total_records = len(nodes_df) + len(edges_df)

        nodes_per_sec = len(nodes_df) / max(0.001, node_load_time)
        rels_per_sec = len(edges_df) / max(0.001, rel_load_time)
        total_records_per_sec = total_records / max(0.001, total_load_time)

        logger.info(
            f"Kùzu loading complete: {len(nodes_df)} nodes in {node_load_time:.2f}s ({nodes_per_sec:.1f} nodes/s), "
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
        # Convert param types if necessary for Kùzu
        res = self._conn.execute(query, params)
        rows = []
        while res.has_next():
            rows.append(res.get_next())
        return rows
