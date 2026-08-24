"""
Script to load dataset into a specific graph database.
"""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from benchmark.cli import main

if __name__ == "__main__":
    if len(sys.argv) < 2 or "--database" not in sys.argv:
        print("Usage: python scripts/load_database.py --database <database_key>")
        sys.exit(1)
    sys.argv = ["benchmark.cli", "load"] + sys.argv[1:]
    main()
