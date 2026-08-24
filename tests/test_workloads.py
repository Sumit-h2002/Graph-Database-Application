"""
Tests for benchmark workloads execution with mock adapter.
"""

import pytest
from benchmark.adapters.mock import MockDatabaseAdapter
from benchmark.workloads import (
    AggregationWorkload,
    FilteredLookupWorkload,
    PointLookupWorkload,
    Traversal1HopWorkload,
    Traversal2HopWorkload,
    Traversal3HopWorkload,
    MixedReadWriteWorkload,
)


@pytest.fixture
def mock_adapter():
    adapter = MockDatabaseAdapter()
    adapter.connect()
    # Populate a few mock nodes
    adapter.nodes = {
        1: {"id": 1, "name": "Paper_1", "category": "Astrophysics", "year": 2000, "weight": 0.5},
        2: {"id": 2, "name": "Paper_2", "category": "Quantum Physics", "year": 2001, "weight": 0.6},
    }
    yield adapter
    adapter.close()


def test_traversal_workloads_execution(mock_adapter):
    wl1 = Traversal1HopWorkload(start_node_ids=[1, 2], warmup_iterations=2, measurement_iterations=5)
    warmup_count = wl1.run_warmup(mock_adapter)
    assert warmup_count == 2

    results = wl1.run_measurement(mock_adapter, run_id="test_run")
    assert len(results) == 5
    assert all(r.success for r in results)
    assert all(r.latency_ms is not None and r.latency_ms > 0 for r in results)


def test_lookup_workloads_execution(mock_adapter):
    point_wl = PointLookupWorkload(node_ids=[1, 2], warmup_iterations=2, measurement_iterations=4)
    point_res = point_wl.run_measurement(mock_adapter, run_id="test_run")
    assert len(point_res) == 4
    assert all(r.success for r in point_res)

    filter_wl = FilteredLookupWorkload(categories=["Astrophysics"], warmup_iterations=1, measurement_iterations=3)
    filter_res = filter_wl.run_measurement(mock_adapter, run_id="test_run")
    assert len(filter_res) == 3
    assert all(r.success for r in filter_res)


def test_aggregation_workload_execution(mock_adapter):
    agg_wl = AggregationWorkload(warmup_iterations=2, measurement_iterations=3)
    res = agg_wl.run_measurement(mock_adapter, run_id="test_run")
    assert len(res) == 3
    assert all(r.success for r in res)


def test_mixed_concurrency_workload(mock_adapter):
    mixed_wl = MixedReadWriteWorkload(
        node_ids=[1, 2],
        categories=["Astrophysics"],
        concurrency_levels=[2, 4],
        read_ratio=0.75,
        write_ratio=0.25,
        duration_seconds=0.5,
        random_seed=42
    )

    res = mixed_wl.run_level(mock_adapter, concurrency=2, run_id="test_run")
    assert res.concurrency == 2
    assert res.total_operations > 0
    assert res.successful_operations > 0
    assert res.throughput_ops_sec > 0
    assert res.p50_ms is not None
