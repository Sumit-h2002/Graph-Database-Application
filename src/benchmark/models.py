"""
Domain models and dataclasses for graph database benchmark framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class BenchmarkResult:
    """Represents a single query execution measurement."""
    database: str
    workload: str
    run_id: str
    iteration: int
    latency_ms: Optional[float]
    latency_ns: Optional[int]
    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    params_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AggregatedResult:
    """Statistical aggregation of multiple iterations for a workload run."""
    database: str
    workload: str
    run_id: str
    iterations: int
    successful_operations: int
    failed_operations: int
    p50_ms: Optional[float]
    p90_ms: Optional[float]
    p95_ms: Optional[float]
    p99_ms: Optional[float]
    mean_ms: Optional[float]
    min_ms: Optional[float]
    max_ms: Optional[float]
    stddev_ms: Optional[float]
    throughput_ops_sec: Optional[float]
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LoadResult:
    """Metrics recorded during the data loading benchmark."""
    database: str
    run_id: str
    nodes_loaded: int
    rels_loaded: int
    total_records: int
    node_load_time_sec: float
    rel_load_time_sec: float
    total_load_time_sec: float
    nodes_per_sec: float
    rels_per_sec: float
    total_records_per_sec: float
    batch_size: int
    success: bool
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MixedWorkloadResult:
    """Metrics recorded during concurrent mixed read/write execution."""
    database: str
    run_id: str
    concurrency: int
    duration_seconds: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    throughput_ops_sec: float
    read_operations: int
    write_operations: int
    read_throughput_ops_sec: float
    write_throughput_ops_sec: float
    p50_ms: Optional[float]
    p95_ms: Optional[float]
    p99_ms: Optional[float]
    error_rate: float
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResourceMetric:
    """Observable hardware and database resource metrics."""
    database: str
    cpu_percent: Optional[float] = None
    memory_used_mb: Optional[float] = None
    memory_total_mb: Optional[float] = None
    database_size_mb: Optional[float] = None
    is_observable: bool = True
    notes: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DatabaseMetadata:
    """Platform documentation and configuration metadata."""
    name: str
    key: str
    version: str
    deployment_type: str
    hosting: str
    region: str
    vcpu: int
    ram_gb: float
    storage_gb: float
    resource_limitations: str
    driver: str
    query_language: str
    indexing_support: str
    import_method: str
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
