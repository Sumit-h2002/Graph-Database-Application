"""
CognDB Cloud Database Adapter using Neo4j/Bolt Python Driver.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from benchmark.adapters.base import GraphDatabaseAdapter
from benchmark.models import DatabaseMetadata, LoadResult

logger = logging.getLogger("benchmark.adapters.cognodb")


class CognDBAdapter(GraphDatabaseAdapter):
    """
    Adapter for CognDB Cloud using Bolt protocol via official neo4j driver.
    """

    def __init__(self, metadata: DatabaseMetadata):
        super().__init__("cognodb", metadata)
        self.uri = os.getenv("COGNODB_URI", "")
        self.username = os.getenv("COGNODB_USERNAME", "cognodb")
        self.password = os.getenv("COGNODB_PASSWORD", "")
        self.database = os.getenv("COGNODB_DATABASE", "neo4j")
        
        # Explicit override only if specified; otherwise driver infers TLS from URI (e.g. bolt+s://)
        enc_env = os.getenv("COGNODB_ENCRYPTED")
        self.encrypted_override = enc_env.lower() in ("true", "1", "yes") if enc_env else None
        self._driver = None

    def connect(self) -> None:
        if not self.uri:
            raise ValueError("Missing required environment variable: COGNODB_URI")
        if not self.password:
            raise ValueError("Missing required environment variable: COGNODB_PASSWORD")

        try:
            from neo4j import GraphDatabase, basic_auth
            auth = basic_auth(self.username, self.password) if self.password else None
            
            driver_kwargs: Dict[str, Any] = {
                "max_connection_lifetime": 300,
                "max_connection_pool_size": 50,
                "connection_acquisition_timeout": 30.0
            }
            if self.encrypted_override is not None:
                driver_kwargs["encrypted"] = self.encrypted_override

            self._driver = GraphDatabase.driver(
                self.uri,
                auth=auth,
                **driver_kwargs
            )
            self._driver.verify_connectivity()
            self.is_connected = True
            logger.info("Connected successfully to CognDB Cloud endpoint.")
        except Exception as e:
            self.is_connected = False
            logger.error(f"Failed to connect to CognDB Cloud: {e}")
            raise

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self.is_connected = False
            logger.info("Closed CognDB connection.")

    def health_check(self) -> bool:
        if not self._driver:
            return False
        try:
            with self._driver.session(database=self.database) as session:
                result = session.run("RETURN 1 AS ping")
                record = result.single()
                return record is not None and record["ping"] == 1
        except Exception as e:
            logger.warning(f"CognDB health check failed: {e}")
            return False

    def clear_database(self) -> None:
        logger.info("Clearing CognDB graph data...")
        with self._driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("CognDB cleared.")

    def create_schema(self) -> None:
        logger.info("Creating indexes and schema constraints in CognDB...")
        with self._driver.session(database=self.database) as session:
            try:
                session.run("CREATE CONSTRAINT paper_id_uniq IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE")
            except Exception:
                try:
                    session.run("CREATE CONSTRAINT ON (p:Paper) ASSERT p.id IS UNIQUE")
                except Exception as e:
                    logger.warning(f"Constraint creation fallback in CognDB: {e}")

            try:
                session.run("CREATE INDEX paper_category_idx IF NOT EXISTS FOR (p:Paper) ON (p.category)")
            except Exception:
                try:
                    session.run("CREATE INDEX ON :Paper(category)")
                except Exception as e:
                    logger.warning(f"Index creation fallback in CognDB: {e}")
        logger.info("CognDB schema & indexes configured.")

    def load_data(
        self,
        nodes_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        batch_size: int = 5000,
        run_id: str = "init"
    ) -> LoadResult:
        logger.info(f"Starting CognDB data loading ({len(nodes_df)} nodes, {len(edges_df)} edges, batch_size={batch_size})...")
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
        with self._driver.session(database=self.database) as session:
            for i in range(0, len(node_records), batch_size):
                batch = node_records[i : i + batch_size]
                session.run(node_query, {"batch": batch})
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
        with self._driver.session(database=self.database) as session:
            for i in range(0, len(edge_records), batch_size):
                batch = edge_records[i : i + batch_size]
                session.run(edge_query, {"batch": batch})
        rel_load_time = time.perf_counter() - start_edges

        total_load_time = time.perf_counter() - start_total
        total_records = len(nodes_df) + len(edges_df)

        nodes_per_sec = len(nodes_df) / max(0.001, node_load_time)
        rels_per_sec = len(edges_df) / max(0.001, rel_load_time)
        total_records_per_sec = total_records / max(0.001, total_load_time)

        logger.info(
            f"CognDB loading complete: {len(nodes_df)} nodes in {node_load_time:.2f}s ({nodes_per_sec:.1f} nodes/s), "
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
        with self._driver.session(database=self.database) as session:
            result = session.run(query, params)
            return result.data()
