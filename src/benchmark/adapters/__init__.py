"""
Database Adapters Module.
"""

from typing import Dict, Type
from benchmark.adapters.base import GraphDatabaseAdapter
from benchmark.adapters.cognodb import CognDBAdapter
from benchmark.adapters.neo4j import Neo4jAdapter
from benchmark.adapters.memgraph import MemgraphAdapter
from benchmark.adapters.falkordb import FalkorDBAdapter
from benchmark.adapters.kuzu import KuzuAdapter
from benchmark.adapters.neptune import NeptuneAdapter
from benchmark.adapters.mock import MockDatabaseAdapter
from benchmark.models import DatabaseMetadata

ADAPTER_REGISTRY: Dict[str, Type[GraphDatabaseAdapter]] = {
    "cognodb": CognDBAdapter,
    "neo4j": Neo4jAdapter,
    "memgraph": MemgraphAdapter,
    "falkordb": FalkorDBAdapter,
    "neptune": NeptuneAdapter,
    "kuzu": KuzuAdapter,
    "mock": MockDatabaseAdapter,
}


def get_adapter(db_key: str, metadata: DatabaseMetadata) -> GraphDatabaseAdapter:
    """Factory function returning the corresponding adapter instance."""
    adapter_cls = ADAPTER_REGISTRY.get(db_key.lower())
    if not adapter_cls:
        raise ValueError(f"Unknown database adapter key: '{db_key}'. Available: {list(ADAPTER_REGISTRY.keys())}")
    return adapter_cls(metadata)


__all__ = [
    "GraphDatabaseAdapter",
    "CognDBAdapter",
    "Neo4jAdapter",
    "MemgraphAdapter",
    "FalkorDBAdapter",
    "NeptuneAdapter",
    "KuzuAdapter",
    "MockDatabaseAdapter",
    "get_adapter",
    "ADAPTER_REGISTRY",
]
