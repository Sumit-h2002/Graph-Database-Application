"""
Pytest configuration and common fixtures for benchmark test suite.
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure src is in python path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from benchmark.config import BenchmarkConfig


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def test_config(project_root: Path) -> BenchmarkConfig:
    return BenchmarkConfig(root_dir=project_root)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)
