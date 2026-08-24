"""
Dataset validation and graph integrity verification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
import pandas as pd

logger = logging.getLogger("benchmark.dataset.validator")


@dataclass
class ValidationReport:
    """Detailed dataset validation report."""
    is_valid: bool
    node_count: int
    relationship_count: int
    unique_nodes: int
    unique_edges: int
    dangling_edges_count: int
    self_loops_count: int
    isolated_nodes_count: int
    avg_degree: float
    max_out_degree: int
    categories_present: List[str]
    errors: List[str]
    warnings: List[str]


class DatasetValidator:
    """Validates structural and semantic correctness of graph datasets."""

    def __init__(
        self,
        min_relationships: int = 100000,
        max_relationships: int = 500000
    ):
        self.min_relationships = min_relationships
        self.max_relationships = max_relationships

    def validate(
        self,
        nodes_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        strict_range: bool = False
    ) -> ValidationReport:
        """Runs comprehensive validation checks on nodes and edges dataframes."""
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Check Node DataFrame
        required_node_cols = {"id", "name", "category", "year", "weight"}
        if not required_node_cols.issubset(set(nodes_df.columns)):
            errors.append(f"Nodes missing required columns: {required_node_cols - set(nodes_df.columns)}")

        node_count = len(nodes_df)
        unique_nodes = nodes_df["id"].nunique() if "id" in nodes_df.columns else 0
        if unique_nodes != node_count:
            errors.append(f"Node IDs are not unique! {node_count} rows but {unique_nodes} unique IDs.")

        # Check nulls in nodes
        if nodes_df.isnull().values.any():
            errors.append("Nodes contain null or NaN values.")

        # 2. Check Edge DataFrame
        required_edge_cols = {"source_id", "target_id", "rel_type", "weight"}
        if not required_edge_cols.issubset(set(edges_df.columns)):
            errors.append(f"Edges missing required columns: {required_edge_cols - set(edges_df.columns)}")

        relationship_count = len(edges_df)
        if strict_range and (relationship_count < self.min_relationships or relationship_count > self.max_relationships):
            errors.append(
                f"Relationship count {relationship_count:,} outside required range "
                f"[{self.min_relationships:,}, {self.max_relationships:,}]."
            )
        elif relationship_count < self.min_relationships or relationship_count > self.max_relationships:
            warnings.append(
                f"Relationship count {relationship_count:,} is outside standard default target "
                f"[{self.min_relationships:,}, {self.max_relationships:,}]."
            )

        # Check nulls in edges
        if edges_df.isnull().values.any():
            errors.append("Edges contain null or NaN values.")

        # 3. Structural Integrity: Dangling edges and self loops
        node_id_set: Set[int] = set(nodes_df["id"].tolist()) if "id" in nodes_df.columns else set()
        src_set: Set[int] = set(edges_df["source_id"].tolist()) if "source_id" in edges_df.columns else set()
        dst_set: Set[int] = set(edges_df["target_id"].tolist()) if "target_id" in edges_df.columns else set()

        dangling_sources = src_set - node_id_set
        dangling_targets = dst_set - node_id_set
        dangling_count = len(dangling_sources) + len(dangling_targets)
        if dangling_count > 0:
            errors.append(f"Found dangling edges referencing non-existent nodes: {dangling_count} missing references.")

        self_loops = (edges_df["source_id"] == edges_df["target_id"]).sum() if "source_id" in edges_df.columns else 0
        if self_loops > 0:
            warnings.append(f"Found {self_loops} self-loops in edges.")

        # Degree calculations
        out_degrees = edges_df["source_id"].value_counts() if "source_id" in edges_df.columns else pd.Series()
        max_out_degree = int(out_degrees.max()) if not out_degrees.empty else 0
        avg_degree = float(relationship_count / max(1, node_count))

        connected_nodes = src_set | dst_set
        isolated_nodes = len(node_id_set - connected_nodes)

        categories = sorted(list(nodes_df["category"].unique())) if "category" in nodes_df.columns else []

        is_valid = len(errors) == 0

        report = ValidationReport(
            is_valid=is_valid,
            node_count=node_count,
            relationship_count=relationship_count,
            unique_nodes=unique_nodes,
            unique_edges=relationship_count,
            dangling_edges_count=dangling_count,
            self_loops_count=int(self_loops),
            isolated_nodes_count=isolated_nodes,
            avg_degree=round(avg_degree, 2),
            max_out_degree=max_out_degree,
            categories_present=categories,
            errors=errors,
            warnings=warnings
        )

        if is_valid:
            logger.info(f"Dataset validation PASSED: {node_count:,} nodes, {relationship_count:,} edges.")
        else:
            logger.error(f"Dataset validation FAILED with {len(errors)} errors: {errors}")

        return report
