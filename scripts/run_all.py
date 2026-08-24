"""
Script to execute the complete end-to-end benchmark pipeline.
"""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from benchmark.cli import main

if __name__ == "__main__":
    sys.argv = ["benchmark.cli", "run-all"] + sys.argv[1:]
    main()
