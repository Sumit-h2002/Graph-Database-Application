"""
Configuration loader and validator for the benchmark framework.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv

from benchmark.models import DatabaseMetadata

# Load .env if present
load_dotenv()


class BenchmarkConfig:
    """Manages parsing, validation, and access to all configuration YAMLs."""

    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            # Assume project root is parent of src/ or current working directory
            self.root_dir = Path.cwd()
        else:
            self.root_dir = Path(root_dir)

        self.config_dir = self.root_dir / "config"
        self._benchmark_raw: Dict[str, Any] = {}
        self._databases_raw: Dict[str, Any] = {}
        self._workloads_raw: Dict[str, Any] = {}

        self.load_all()

    def load_all(self) -> None:
        """Loads and parses all YAML configuration files."""
        self._benchmark_raw = self._load_yaml(self.config_dir / "benchmark.yaml")
        self._databases_raw = self._load_yaml(self.config_dir / "databases.yaml")
        self._workloads_raw = self._load_yaml(self.config_dir / "workloads.yaml")

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}

    # Dataset configs
    @property
    def dataset_name(self) -> str:
        return self._benchmark_raw.get("dataset", {}).get("name", "cit-HepPh")

    @property
    def dataset_source_url(self) -> str:
        return self._benchmark_raw.get("dataset", {}).get("source_url", "")

    @property
    def random_seed(self) -> int:
        env_seed = os.getenv("BENCHMARK_RANDOM_SEED")
        if env_seed and env_seed.isdigit():
            return int(env_seed)
        return int(self._benchmark_raw.get("dataset", {}).get("random_seed", 42))

    @property
    def target_nodes(self) -> int:
        return int(self._benchmark_raw.get("dataset", {}).get("target_nodes", 34546))

    @property
    def target_relationships(self) -> int:
        return int(self._benchmark_raw.get("dataset", {}).get("target_relationships", 421578))

    @property
    def raw_data_dir(self) -> Path:
        rel = self._benchmark_raw.get("dataset", {}).get("raw_dir", "data/raw")
        return (self.root_dir / rel).resolve()

    @property
    def processed_data_dir(self) -> Path:
        rel = self._benchmark_raw.get("dataset", {}).get("processed_dir", "data/processed")
        return (self.root_dir / rel).resolve()

    @property
    def default_batch_size(self) -> int:
        return int(self._benchmark_raw.get("dataset", {}).get("batch_size", 5000))

    # Benchmark execution configs
    @property
    def warmup_iterations(self) -> int:
        return int(self._benchmark_raw.get("benchmark", {}).get("warmup_iterations", 20))

    @property
    def measurement_iterations(self) -> int:
        return int(self._benchmark_raw.get("benchmark", {}).get("measurement_iterations", 100))

    @property
    def repetitions(self) -> int:
        return int(self._benchmark_raw.get("benchmark", {}).get("repetitions", 3))

    @property
    def timeout_seconds(self) -> int:
        return int(self._benchmark_raw.get("benchmark", {}).get("timeout_seconds", 120))

    @property
    def results_dir(self) -> Path:
        rel = self._benchmark_raw.get("benchmark", {}).get("results_dir", "results")
        return (self.root_dir / rel).resolve()

    @property
    def raw_results_dir(self) -> Path:
        rel = self._benchmark_raw.get("reporting", {}).get("raw_dir", "results/raw")
        return (self.root_dir / rel).resolve()

    @property
    def processed_results_dir(self) -> Path:
        rel = self._benchmark_raw.get("reporting", {}).get("processed_dir", "results/processed")
        return (self.root_dir / rel).resolve()

    @property
    def charts_dir(self) -> Path:
        rel = self._benchmark_raw.get("reporting", {}).get("charts_dir", "results/charts")
        return (self.root_dir / rel).resolve()

    # Databases
    def get_database_configs(self) -> Dict[str, DatabaseMetadata]:
        dbs = {}
        for key, info in self._databases_raw.get("databases", {}).items():
            dbs[key] = DatabaseMetadata(
                name=info.get("name", key),
                key=key,
                version=info.get("version", "unknown"),
                deployment_type=info.get("deployment_type", "unknown"),
                hosting=info.get("hosting", "cloud/local"),
                region=info.get("region", "us-east-1"),
                vcpu=int(info.get("vcpu", 2)),
                ram_gb=float(info.get("ram_gb", 4.0)),
                storage_gb=float(info.get("storage_gb", 20.0)),
                resource_limitations=info.get("resource_limitations", "None specified"),
                driver=info.get("driver", "generic"),
                query_language=info.get("query_language", "Cypher"),
                indexing_support=info.get("indexing_support", "Standard"),
                import_method=info.get("import_method", "Batched inserts"),
                enabled=bool(info.get("enabled", True)),
            )
        return dbs

    def get_database_config(self, key: str) -> Optional[DatabaseMetadata]:
        dbs = self.get_database_configs()
        return dbs.get(key)

    def validate_database_environment(self, db_key: str) -> List[str]:
        """
        Validates whether required environment variables for a specific database are present.
        Returns a list of missing variable error messages.
        """
        errors = []
        key = db_key.lower()
        if key == "cognodb":
            if not os.getenv("COGNODB_URI"):
                errors.append("Missing required environment variable: COGNODB_URI")
            if not os.getenv("COGNODB_PASSWORD"):
                errors.append("Missing required environment variable: COGNODB_PASSWORD")
        elif key == "neo4j":
            if not os.getenv("NEO4J_URI"):
                errors.append("Missing required environment variable: NEO4J_URI")
            if not os.getenv("NEO4J_PASSWORD"):
                errors.append("Missing required environment variable: NEO4J_PASSWORD")
        elif key == "memgraph":
            if not os.getenv("MEMGRAPH_URI"):
                errors.append("Missing required environment variable: MEMGRAPH_URI")
        elif key == "falkordb":
            if not os.getenv("FALKORDB_URI") and not os.getenv("FALKORDB_HOST"):
                errors.append("Missing required environment variable: FALKORDB_URI (or FALKORDB_HOST)")
        elif key == "kuzu":
            # Kuzu defaults to data/kuzu_db if not explicitly set
            pass
        return errors

    # Workloads
    def get_workloads_config(self) -> Dict[str, Any]:
        return self._workloads_raw.get("workloads", {})

    def get_mixed_workload_config(self) -> Dict[str, Any]:
        return self.get_workloads_config().get("mixed_workload", {
            "concurrency_levels": [10, 20, 40],
            "read_ratio": 0.8,
            "write_ratio": 0.2,
            "duration_seconds": 30,
        })
