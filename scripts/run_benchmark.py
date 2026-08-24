"""
Script to execute benchmarks against a database or all enabled databases.
"""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from benchmark.cli import main

if __name__ == "__main__":
    sys.argv = ["benchmark.cli", "benchmark"] + sys.argv[1:]
    main()
