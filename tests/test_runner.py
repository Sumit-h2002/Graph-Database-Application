"""
Tests for BenchmarkRunner coordination and end-to-end flow.
"""

from pathlib import Path
import pandas as pd
import pytest

from benchmark.adapters.mock import MockDatabaseAdapter
from benchmark.config import BenchmarkConfig
from benchmark.dataset import DatasetGenerator
from benchmark.runner import BenchmarkRunner


@pytest.fixture
def runner_with_dataset(temp_dir: Path, test_config: BenchmarkConfig):
    # Setup test dataset in temp_dir
    test_config.config_dir = test_config.root_dir / "config"
    # Override directories
    test_config._benchmark_raw["dataset"]["processed_dir"] = str(temp_dir / "processed")
    test_config._benchmark_raw["dataset"]["raw_dir"] = str(temp_dir / "raw")
    test_config._benchmark_raw["benchmark"]["results_dir"] = str(temp_dir / "results")
    test_config._benchmark_raw["reporting"]["raw_dir"] = str(temp_dir / "results" / "raw")
    test_config._benchmark_raw["reporting"]["processed_dir"] = str(temp_dir / "results" / "processed")
    test_config._benchmark_raw["reporting"]["charts_dir"] = str(temp_dir / "results" / "charts")
    test_config._benchmark_raw["benchmark"]["warmup_iterations"] = 2
    test_config._benchmark_raw["benchmark"]["measurement_iterations"] = 5
    test_config._benchmark_raw["benchmark"]["repetitions"] = 1
    test_config._workloads_raw["workloads"]["mixed_workload"]["concurrency_levels"] = [2]
    test_config._workloads_raw["workloads"]["mixed_workload"]["duration_seconds"] = 0.5

    gen = DatasetGenerator(
        processed_dir=test_config.processed_data_dir,
        random_seed=42,
        target_nodes=100,
        target_relationships=300
    )
    gen.process_and_save()

    runner = BenchmarkRunner(test_config)
    return runner


def test_runner_executes_mock_benchmark(runner_with_dataset: BenchmarkRunner):
    runner = runner_with_dataset
    mock_adapter = MockDatabaseAdapter(db_key="mock")

    results = runner.run_database_benchmark(db_key="mock", adapter_override=mock_adapter)

    assert results["database"] == "mock"
    assert len(results["load_results"]) == 1
    assert len(results["aggregated_results"]) >= 6  # point, filter, 3 traversals, agg
    assert len(results["mixed_results"]) == 1
    assert len(results["resource_metrics"]) == 2

    # Check persisted files
    raw_files = list(runner.config.raw_results_dir.rglob("*.jsonl"))
    assert len(raw_files) >= 6

    summary_csv = runner.config.processed_results_dir / "aggregated_summary.csv"
    assert summary_csv.exists()
    df_summary = pd.read_csv(summary_csv)
    assert not df_summary.empty
    assert "p50_ms" in df_summary.columns
    assert "p95_ms" in df_summary.columns
