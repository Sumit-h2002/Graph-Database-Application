# Benchmark Data Directory

This directory stores raw and processed graph datasets.

- `raw/`: Downloaded raw SNAP dataset archives (e.g. `cit-HepPh.txt.gz`).
- `processed/`: Standardized, validated, and normalized CSV datasets:
  - `nodes.csv`: Standardized node table (`id: int`, `name: str`, `category: str`, `year: int`, `weight: float`)
  - `edges.csv`: Standardized relationship table (`source_id: int`, `target_id: int`, `rel_type: str`, `weight: float`)
  - `metadata.json`: Dataset statistics, deterministic seed, and sampling metadata.
