"""
Dataset loader, generator, and validator module for benchmark graph data.
"""

from benchmark.dataset.loader import DatasetLoader
from benchmark.dataset.generator import DatasetGenerator
from benchmark.dataset.validator import DatasetValidator

# Aliases for compatibility
DatasetDownloader = DatasetLoader
GraphGenerator = DatasetGenerator

__all__ = [
    "DatasetLoader",
    "DatasetDownloader",
    "DatasetGenerator",
    "GraphGenerator",
    "DatasetValidator"
]
