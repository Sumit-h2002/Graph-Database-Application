"""
Tests for benchmark configuration loader, YAML parsing, and database metadata.
"""

from benchmark.config import BenchmarkConfig


def test_benchmark_config_loads_defaults(test_config: BenchmarkConfig):
    assert test_config.dataset_name == "cit-HepPh"
    assert test_config.random_seed == 42
    assert test_config.target_relationships > 100000
    assert test_config.warmup_iterations == 20
    assert test_config.measurement_iterations == 100
    assert test_config.repetitions == 3


def test_database_configs_presence(test_config: BenchmarkConfig):
    dbs = test_config.get_database_configs()
    expected_dbs = ["cognodb", "neo4j", "memgraph", "falkordb", "kuzu"]
    for db_key in expected_dbs:
        assert db_key in dbs, f"Missing database configuration for {db_key}"
        db = dbs[db_key]
        assert db.name is not None
        assert db.version is not None
        assert db.driver is not None
        assert db.query_language is not None
        assert db.vcpu > 0
        assert db.ram_gb > 0


def test_workload_configs(test_config: BenchmarkConfig):
    workloads = test_config.get_workloads_config()
    required_workloads = [
        "loading",
        "traversal_1_hop",
        "traversal_2_hop",
        "traversal_3_hop",
        "point_lookup",
        "filtered_lookup",
        "aggregation",
        "mixed_workload",
    ]
    for wl in required_workloads:
        assert wl in workloads, f"Missing workload specification for {wl}"

    mixed = test_config.get_mixed_workload_config()
    assert 10 in mixed["concurrency_levels"]
    assert 20 in mixed["concurrency_levels"]
    assert 40 in mixed["concurrency_levels"]
    assert mixed["read_ratio"] + mixed["write_ratio"] == 1.0
