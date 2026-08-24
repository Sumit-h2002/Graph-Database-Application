"""
Tests for statistical percentile calculations and result persistence.
"""

from pathlib import Path
import numpy as np
import pytest

from benchmark.models import BenchmarkResult
from benchmark.statistics import ResultStore, calculate_aggregated_result


def test_percentile_calculations_deterministic():
    # 100 observations with known latencies from 1.0ms to 100.0ms
    raw_results = [
        BenchmarkResult(
            database="test_db",
            workload="point_lookup",
            run_id="run_1",
            iteration=i,
            latency_ms=float(i),
            latency_ns=i * 1_000_000,
            success=True
        )
        for i in range(1, 101)
    ]

    agg = calculate_aggregated_result(raw_results, total_elapsed_sec=1.0)

    assert agg.database == "test_db"
    assert agg.workload == "point_lookup"
    assert agg.iterations == 100
    assert agg.successful_operations == 100
    assert agg.failed_operations == 0

    # Percentiles for 1..100
    assert agg.p50_ms == pytest.approx(50.5, 0.1)
    assert agg.p90_ms == pytest.approx(90.1, 0.1)
    assert agg.p95_ms == pytest.approx(95.05, 0.1)
    assert agg.p99_ms == pytest.approx(99.01, 0.1)
    assert agg.min_ms == 1.0
    assert agg.max_ms == 100.0
    assert agg.mean_ms == 50.5
    assert agg.throughput_ops_sec == 100.0


def test_statistics_with_failures_and_errors():
    raw_results = [
        BenchmarkResult(
            database="test_db",
            workload="traversal_1_hop",
            run_id="run_1",
            iteration=1,
            latency_ms=10.0,
            latency_ns=10_000_000,
            success=True
        ),
        BenchmarkResult(
            database="test_db",
            workload="traversal_1_hop",
            run_id="run_1",
            iteration=2,
            latency_ms=None,
            latency_ns=None,
            success=False,
            error_type="TimeoutError",
            error_message="Query timed out"
        ),
        BenchmarkResult(
            database="test_db",
            workload="traversal_1_hop",
            run_id="run_1",
            iteration=3,
            latency_ms=20.0,
            latency_ns=20_000_000,
            success=True
        ),
    ]

    agg = calculate_aggregated_result(raw_results)

    assert agg.iterations == 3
    assert agg.successful_operations == 2
    assert agg.failed_operations == 1
    assert agg.error_breakdown.get("TimeoutError") == 1
    assert agg.p50_ms == 15.0
    assert agg.min_ms == 10.0
    assert agg.max_ms == 20.0


def test_result_store_raw_and_summary(temp_dir: Path):
    store = ResultStore(raw_dir=temp_dir / "raw", processed_dir=temp_dir / "processed")

    raw_items = [
        BenchmarkResult(
            database="mock_db",
            workload="lookup",
            run_id="r1",
            iteration=1,
            latency_ms=5.0,
            latency_ns=5_000_000,
            success=True
        )
    ]
    raw_path = store.save_raw_results("mock_db", "r1", "lookup", raw_items)
    assert raw_path.exists()

    agg = calculate_aggregated_result(raw_items)
    csv_path = store.save_aggregated_summary([agg])
    assert csv_path.exists()
