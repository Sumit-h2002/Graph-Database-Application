"""
Dataset generator and preprocessor for standardizing graph data.
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger("benchmark.dataset.generator")

CATEGORIES = [
    "Astrophysics",
    "High Energy Physics - Theory",
    "High Energy Physics - Phenomenology",
    "Quantum Gravity",
    "String Theory",
    "Nuclear Theory",
    "General Relativity",
    "Quantum Physics"
]


class DatasetGenerator:
    """Preprocesses raw SNAP graph data into standardized, normalized tables."""

    def __init__(
        self,
        processed_dir: Path,
        random_seed: int = 42,
        target_nodes: int = 34546,
        target_relationships: int = 421578,
    ):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.random_seed = random_seed
        self.target_nodes = target_nodes
        self.target_relationships = target_relationships
        self.rng = random.Random(random_seed)
        np.random.seed(random_seed)

    def process_and_save(
        self,
        raw_edges: Optional[List[Tuple[int, int]]] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """Converts raw edges or generates deterministic graph, then writes CSVs."""
        if raw_edges and len(raw_edges) > 0:
            logger.info(f"Processing {len(raw_edges)} raw edges with seed {self.random_seed}...")
            nodes_df, edges_df = self._process_raw_edges(raw_edges)
        else:
            logger.info(f"Generating deterministic synthetic graph ({self.target_nodes} nodes, {self.target_relationships} rels)...")
            nodes_df, edges_df = self._generate_synthetic_graph()

        # Save standardized CSVs
        nodes_path = self.processed_dir / "nodes.csv"
        edges_path = self.processed_dir / "edges.csv"
        metadata_path = self.processed_dir / "metadata.json"

        nodes_df.to_csv(nodes_path, index=False)
        edges_df.to_csv(edges_path, index=False)

        metadata = {
            "name": "cit-HepPh-standardized",
            "random_seed": self.random_seed,
            "node_count": len(nodes_df),
            "relationship_count": len(edges_df),
            "categories": CATEGORIES,
            "node_columns": list(nodes_df.columns),
            "edge_columns": list(edges_df.columns),
            "min_year": int(nodes_df["year"].min()),
            "max_year": int(nodes_df["year"].max()),
            "avg_out_degree": float(len(edges_df) / max(1, len(nodes_df))),
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info(
            f"Dataset saved to {self.processed_dir}: "
            f"{len(nodes_df):,} nodes, {len(edges_df):,} edges."
        )
        return nodes_df, edges_df, metadata

    def _process_raw_edges(
        self,
        raw_edges: List[Tuple[int, int]]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Normalizes node IDs, filters duplicates/self-loops, and attaches metadata."""
        # Deduplicate and remove self-loops
        unique_edges: Set[Tuple[int, int]] = set()
        for src, dst in raw_edges:
            if src != dst:
                unique_edges.add((src, dst))

        edge_list = list(unique_edges)

        # Deterministic sampling if edge count is larger than desired target
        if len(edge_list) > self.target_relationships:
            self.rng.shuffle(edge_list)
            edge_list = edge_list[:self.target_relationships]

        # Extract all participating unique nodes
        unique_node_ids = sorted(list({src for src, _ in edge_list} | {dst for _, dst in edge_list}))

        # Remap sparse node IDs to dense 1..N range for clean indexing & consistent lookup
        id_map = {old_id: idx + 1 for idx, old_id in enumerate(unique_node_ids)}

        # Build normalized node records
        node_records = []
        for old_id, new_id in id_map.items():
            cat = self.rng.choice(CATEGORIES)
            year = self.rng.randint(1992, 2003)
            weight = round(self.rng.uniform(0.1, 1.0), 3)
            node_records.append({
                "id": new_id,
                "name": f"Paper_{new_id}",
                "category": cat,
                "year": year,
                "weight": weight,
                "original_id": old_id
            })

        # Build normalized edge records
        edge_records = []
        for src, dst in edge_list:
            mapped_src = id_map[src]
            mapped_dst = id_map[dst]
            rel_weight = round(self.rng.uniform(0.1, 1.0), 3)
            edge_records.append({
                "source_id": mapped_src,
                "target_id": mapped_dst,
                "rel_type": "CITES",
                "weight": rel_weight
            })

        nodes_df = pd.DataFrame(node_records)
        edges_df = pd.DataFrame(edge_records)

        return nodes_df, edges_df

    def _generate_synthetic_graph(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generates deterministic scale-free graph matching SNAP citation properties."""
        n_nodes = self.target_nodes
        n_edges = self.target_relationships
        avg_degree = max(2, n_edges // n_nodes)

        # Generate scale-free preferential attachment edges deterministically
        edge_set: Set[Tuple[int, int]] = set()

        # Seed initial clique
        init_clique = 5
        for i in range(1, init_clique + 1):
            for j in range(1, init_clique + 1):
                if i != j:
                    edge_set.add((i, j))

        node_targets = list(range(1, init_clique + 1)) * (init_clique - 1)

        for source in range(init_clique + 1, n_nodes + 1):
            # Select targets with preferential attachment
            targets = set()
            attempts = 0
            while len(targets) < min(avg_degree, len(set(node_targets))) and attempts < avg_degree * 5:
                attempts += 1
                chosen = self.rng.choice(node_targets)
                if chosen != source:
                    targets.add(chosen)

            for target in targets:
                edge_set.add((source, target))
                node_targets.append(source)
                node_targets.append(target)

        # Fill remaining edges deterministically if needed
        all_nodes = list(range(1, n_nodes + 1))
        while len(edge_set) < n_edges:
            src = self.rng.choice(all_nodes)
            dst = self.rng.choice(all_nodes)
            if src != dst:
                edge_set.add((src, dst))

        edge_list = list(edge_set)[:n_edges]

        # Build node and edge dataframes
        node_records = []
        for node_id in range(1, n_nodes + 1):
            cat = self.rng.choice(CATEGORIES)
            year = self.rng.randint(1992, 2003)
            weight = round(self.rng.uniform(0.1, 1.0), 3)
            node_records.append({
                "id": node_id,
                "name": f"Paper_{node_id}",
                "category": cat,
                "year": year,
                "weight": weight,
                "original_id": node_id
            })

        edge_records = []
        for src, dst in edge_list:
            edge_records.append({
                "source_id": src,
                "target_id": dst,
                "rel_type": "CITES",
                "weight": round(self.rng.uniform(0.1, 1.0), 3)
            })

        nodes_df = pd.DataFrame(node_records)
        edges_df = pd.DataFrame(edge_records)

        return nodes_df, edges_df
