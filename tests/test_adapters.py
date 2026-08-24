"""
Tests for database adapter abstraction and contract compliance.
"""

import pandas as pd
import pytest

from benchmark.adapters import (
    ADAPTER_REGISTRY,
    CognDBAdapter,
    FalkorDBAdapter,
    KuzuAdapter,
    MemgraphAdapter,
    MockDatabaseAdapter,
    Neo4jAdapter,
    get_adapter,
)
from benchmark.models import DatabaseMetadata


def test_adapter_registry():
    expected_keys = ["cognodb", "neo4j", "memgraph", "falkordb", "kuzu", "mock"]
    for key in expected_keys:
        assert key in ADAPTER_REGISTRY


def test_mock_adapter_lifecycle():
    adapter = MockDatabaseAdapter(db_key="test_mock")
    assert not adapter.is_connected

    adapter.connect()
    assert adapter.is_connected
    assert adapter.health_check()

    adapter.create_schema()
    assert adapter.schema_created

    nodes_df = pd.DataFrame([{"id": 1, "name": "Paper 1", "category": "A", "year": 2000, "weight": 0.5}])
    edges_df = pd.DataFrame([{"source_id": 1, "target_id": 1, "rel_type": "CITES", "weight": 0.5}])

    load_res = adapter.load_data(nodes_df, edges_df, batch_size=10, run_id="r1")
    assert load_res.success
    assert load_res.nodes_loaded == 1
    assert load_res.rels_loaded == 1

    res = adapter.execute_query("MATCH (n:Paper {id: $node_id})", {"node_id": 1})
    assert len(res) == 1

    usage = adapter.get_resource_usage()
    assert usage.is_observable

    adapter.clear_database()
    assert len(adapter.nodes) == 0

    adapter.close()
    assert not adapter.is_connected


def test_kuzu_adapter_in_memory_or_temp(temp_dir):
    meta = DatabaseMetadata(
        name="Kùzu Test",
        key="kuzu",
        version="test",
        deployment_type="Embedded",
        hosting="local",
        region="local",
        vcpu=2,
        ram_gb=2.0,
        storage_gb=5.0,
        resource_limitations="None",
        driver="kuzu",
        query_language="Cypher",
        indexing_support="PK Hash",
        import_method="COPY",
        enabled=True
    )
    db_path = temp_dir / "test_kuzu_db"
    import os
    os.environ["KUZU_DATABASE_PATH"] = str(db_path)

    adapter = KuzuAdapter(meta)
    adapter.connect()
    assert adapter.is_connected
    assert adapter.health_check()

    adapter.clear_database()
    adapter.create_schema()

    nodes_df = pd.DataFrame([
        {"id": 101, "name": "Paper_101", "category": "Astrophysics", "year": 1999, "weight": 0.8},
        {"id": 102, "name": "Paper_102", "category": "Quantum Physics", "year": 2001, "weight": 0.9}
    ])
    edges_df = pd.DataFrame([
        {"source_id": 101, "target_id": 102, "rel_type": "CITES", "weight": 0.5}
    ])

    load_res = adapter.load_data(nodes_df, edges_df, run_id="test_kuzu_run")
    assert load_res.success
    assert load_res.nodes_loaded == 2
    assert load_res.rels_loaded == 1

    res = adapter.execute_query("MATCH (n:Paper {id: $node_id}) RETURN n.id, n.name", {"node_id": 101})
    assert len(res) == 1
    assert res[0][0] == 101

    adapter.close()
