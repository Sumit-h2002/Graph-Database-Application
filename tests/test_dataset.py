"""
Tests for dataset loader, generator, and validator.
"""

from pathlib import Path
import pandas as pd
import pytest

from benchmark.dataset.generator import DatasetGenerator
from benchmark.dataset.validator import DatasetValidator


def test_synthetic_graph_generation_and_validation(temp_dir: Path):
    generator = DatasetGenerator(
        processed_dir=temp_dir,
        random_seed=42,
        target_nodes=1000,
        target_relationships=5000
    )
    nodes_df, edges_df, metadata = generator.process_and_save()

    assert len(nodes_df) == 1000
    assert len(edges_df) == 5000
    assert metadata["node_count"] == 1000
    assert metadata["relationship_count"] == 5000

    validator = DatasetValidator(min_relationships=1000, max_relationships=10000)
    report = validator.validate(nodes_df, edges_df, strict_range=True)

    assert report.is_valid is True
    assert len(report.errors) == 0
    assert report.unique_nodes == 1000
    assert report.dangling_edges_count == 0
    assert report.avg_degree == 5.0
    assert len(report.categories_present) > 0


def test_deterministic_seed_consistency(temp_dir: Path):
    gen1 = DatasetGenerator(processed_dir=temp_dir / "run1", random_seed=42, target_nodes=500, target_relationships=1500)
    nodes1, edges1, _ = gen1.process_and_save()

    gen2 = DatasetGenerator(processed_dir=temp_dir / "run2", random_seed=42, target_nodes=500, target_relationships=1500)
    nodes2, edges2, _ = gen2.process_and_save()

    pd.testing.assert_frame_equal(nodes1, nodes2)
    pd.testing.assert_frame_equal(edges1, edges2)


def test_validator_detects_dangling_edges():
    nodes_df = pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["A", "B", "C"],
        "category": ["Cat1", "Cat2", "Cat1"],
        "year": [2000, 2001, 2002],
        "weight": [0.5, 0.6, 0.7]
    })
    # Edge points to node 99 which does not exist in nodes_df
    edges_df = pd.DataFrame({
        "source_id": [1, 2],
        "target_id": [2, 99],
        "rel_type": ["CITES", "CITES"],
        "weight": [0.5, 0.5]
    })

    validator = DatasetValidator(min_relationships=1, max_relationships=10)
    report = validator.validate(nodes_df, edges_df, strict_range=False)

    assert report.is_valid is False
    assert report.dangling_edges_count == 1
    assert any("dangling" in err.lower() for err in report.errors)
