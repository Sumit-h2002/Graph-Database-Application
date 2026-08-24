"""
Dataset loader for public SNAP graph datasets with automatic caching.
"""

from __future__ import annotations

import gzip
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import requests

logger = logging.getLogger("benchmark.dataset.loader")


class DatasetLoader:
    """Handles downloading and raw parsing of SNAP citation graphs."""

    DEFAULT_URL = "https://snap.stanford.edu/data/cit-HepPh.txt.gz"

    def __init__(self, raw_dir: Path, source_url: Optional[str] = None):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.source_url = source_url or self.DEFAULT_URL

    def download_if_missing(self) -> Path:
        """Downloads the compressed dataset archive if not already cached locally."""
        filename = self.source_url.split("/")[-1]
        target_path = self.raw_dir / filename

        if target_path.exists() and target_path.stat().st_size > 0:
            logger.info(f"Using cached raw dataset: {target_path} ({target_path.stat().st_size / 1024 / 1024:.2f} MB)")
            return target_path

        logger.info(f"Downloading dataset from {self.source_url} to {target_path}...")
        try:
            response = requests.get(self.source_url, stream=True, timeout=60)
            response.raise_for_status()

            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Download complete: {target_path} ({target_path.stat().st_size / 1024 / 1024:.2f} MB)")
            return target_path
        except Exception as e:
            logger.warning(f"Failed to download from {self.source_url}: {e}. Local fallback generator will be available.")
            if target_path.exists():
                target_path.unlink()
            raise

    def load_raw_edges(self, file_path: Optional[Path] = None) -> List[Tuple[int, int]]:
        """Parses edge list from gz or plain text file."""
        path = file_path or self.download_if_missing()
        edges: List[Tuple[int, int]] = []

        is_gzip = str(path).endswith(".gz")
        open_fn = gzip.open if is_gzip else open

        with open_fn(path, "rt", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        src = int(parts[0])
                        dst = int(parts[1])
                        edges.append((src, dst))
                    except ValueError:
                        continue

        logger.info(f"Parsed {len(edges)} raw edges from {path}")
        return edges
