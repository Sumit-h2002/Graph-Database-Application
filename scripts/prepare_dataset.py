"""
Script to prepare and validate the standardized graph dataset.
"""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from benchmark.cli import main

if __name__ == "__main__":
    sys.argv = ["benchmark.cli", "prepare-data"] + sys.argv[1:]
    main()
