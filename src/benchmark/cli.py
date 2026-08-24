"""
Command-line interface (CLI) for Graph Database Cloud Benchmarking.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from benchmark.config import BenchmarkConfig
from benchmark.dataset import DatasetGenerator, DatasetLoader, DatasetValidator
from benchmark.logging_config import setup_logging
from benchmark.reporter import BenchmarkReporter
from benchmark.runner import BenchmarkRunner

logger = logging.getLogger("benchmark.cli")


def cmd_validate(config: BenchmarkConfig, args: argparse.Namespace) -> int:
    """Validates configuration, environment variables, and dataset integrity."""
    logger.info("Validating benchmark environment and configuration...")
    dbs = config.get_database_configs()
    logger.info(f"Available database adapters ({len(dbs)}): {', '.join(dbs.keys())}")

    # Check environment variable readiness for each database
    for db_key in dbs.keys():
        missing = config.validate_database_environment(db_key)
        if missing:
            logger.info(f"Database '{db_key}': Not fully configured in environment (requires credentials in .env to run).")
        else:
            logger.info(f"Database '{db_key}': Environment configuration READY.")

    nodes_path = config.processed_data_dir / "nodes.csv"
    edges_path = config.processed_data_dir / "edges.csv"

    if nodes_path.exists() and edges_path.exists():
        import pandas as pd
        nodes_df = pd.read_csv(nodes_path)
        edges_df = pd.read_csv(edges_path)
        validator = DatasetValidator(min_relationships=100000, max_relationships=500000)
        report = validator.validate(nodes_df, edges_df, strict_range=False)
        if not report.is_valid:
            logger.error(f"Dataset validation failed: {report.errors}")
            return 1
        logger.info(f"Dataset integrity check PASSED ({report.node_count:,} nodes, {report.relationship_count:,} edges).")
    else:
        logger.warning("Processed dataset not yet found. Run 'prepare-data' command to generate it.")

    logger.info("Environment and configuration validation check complete.")
    return 0


def cmd_prepare_data(config: BenchmarkConfig, args: argparse.Namespace) -> int:
    """Downloads raw SNAP citation graph or creates deterministic dataset."""
    logger.info(f"Preparing dataset with random seed {config.random_seed}...")
    loader = DatasetLoader(raw_dir=config.raw_data_dir, source_url=config.dataset_source_url)
    generator = DatasetGenerator(
        processed_dir=config.processed_data_dir,
        random_seed=config.random_seed,
        target_nodes=config.target_nodes,
        target_relationships=config.target_relationships
    )

    raw_edges = []
    if not getattr(args, "synthetic_only", False):
        try:
            raw_edges = loader.load_raw_edges()
        except Exception as e:
            logger.warning(f"Could not load raw SNAP edges ({e}). Falling back to deterministic synthetic generation.")

    nodes_df, edges_df, _ = generator.process_and_save(raw_edges=raw_edges)

    validator = DatasetValidator(min_relationships=100000, max_relationships=500000)
    report = validator.validate(nodes_df, edges_df, strict_range=False)

    if not report.is_valid:
        logger.error(f"Prepared dataset failed validation: {report.errors}")
        return 1

    logger.info(f"Dataset successfully prepared: {len(nodes_df):,} nodes, {len(edges_df):,} edges.")
    return 0


def cmd_load(config: BenchmarkConfig, args: argparse.Namespace) -> int:
    """Loads dataset into a specified database."""
    runner = BenchmarkRunner(config)
    db_key = args.database.lower()
    nodes_df, edges_df, _ = runner.load_dataset()

    from benchmark.adapters import get_adapter
    db_meta = config.get_database_config(db_key)
    if not db_meta:
        logger.error(f"Unknown database: {db_key}")
        return 1

    adapter = get_adapter(db_key, db_meta)
    try:
        adapter.connect()
        adapter.clear_database()
        adapter.create_schema()
        from benchmark.workloads.loading import LoadingWorkload
        loader = LoadingWorkload(batch_size=config.default_batch_size)
        res = loader.run(adapter, nodes_df, edges_df, run_id="manual_load")
        runner.result_store.save_load_results([res])
        logger.info(f"Loaded {db_key}: {res.nodes_loaded} nodes, {res.rels_loaded} edges in {res.total_load_time_sec:.2f}s")
        return 0
    finally:
        adapter.close()


def cmd_benchmark(config: BenchmarkConfig, args: argparse.Namespace) -> int:
    """Runs benchmark workloads against specified database or all enabled databases."""
    runner = BenchmarkRunner(config)
    target_dbs = []

    if getattr(args, "all", False) or args.database == "all":
        dbs = config.get_database_configs()
        target_dbs = [k for k, v in dbs.items() if v.enabled]
    else:
        target_dbs = [args.database.lower()]

    logger.info(f"Target benchmark databases: {', '.join(target_dbs)}")

    for db_key in target_dbs:
        try:
            runner.run_database_benchmark(db_key=db_key, skip_load=getattr(args, "skip_load", False))
        except Exception as e:
            logger.error(f"Benchmark failed for database '{db_key}': {e}")

    # Automatically generate reports if requested
    reporter = BenchmarkReporter(config)
    reporter.generate_all_charts()
    reporter.generate_markdown_report()
    return 0


def cmd_report(config: BenchmarkConfig, args: argparse.Namespace) -> int:
    """Generates charts and markdown summary reports from recorded results."""
    reporter = BenchmarkReporter(config)
    reporter.generate_all_charts()
    report_file = reporter.generate_markdown_report()
    logger.info(f"Report generation complete: {report_file}")
    return 0


def cmd_run_all(config: BenchmarkConfig, args: argparse.Namespace) -> int:
    """Runs complete end-to-end benchmarking pipeline."""
    logger.info("==================================================================")
    logger.info("Executing Complete End-to-End Graph Database Benchmark Pipeline")
    logger.info("==================================================================")

    # 1. Validate
    v_code = cmd_validate(config, args)
    if v_code != 0:
        return v_code

    # 2. Prepare Data
    nodes_path = config.processed_data_dir / "nodes.csv"
    if not nodes_path.exists():
        p_code = cmd_prepare_data(config, args)
        if p_code != 0:
            return p_code

    # 3. Benchmark
    args.all = True
    args.skip_load = False
    b_code = cmd_benchmark(config, args)

    # 4. Report
    cmd_report(config, args)
    logger.info("Pipeline execution finished.")
    return b_code


def main() -> None:
    setup_logging()
    config = BenchmarkConfig()

    parser = argparse.ArgumentParser(
        prog="python -m benchmark.cli",
        description="Graph Database Cloud Benchmarking Suite (CognDB, Neo4j, Memgraph, FalkorDB, Kùzu)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # validate
    subparsers.add_parser("validate", help="Validate config, environment variables, and dataset integrity")

    # prepare-data
    p_data = subparsers.add_parser("prepare-data", help="Download and prepare standardized dataset")
    p_data.add_argument("--synthetic-only", action="store_true", help="Force synthetic deterministic generation without download")

    # load
    p_load = subparsers.add_parser("load", help="Load dataset into a single database")
    p_load.add_argument("--database", required=True, help="Target database key (e.g. cognodb, neo4j, memgraph, falkordb, kuzu)")

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run benchmark suite")
    p_bench.add_argument("--database", help="Target database key (e.g. cognodb, neo4j, memgraph, falkordb, kuzu, mock)")
    p_bench.add_argument("--all", action="store_true", help="Benchmark all enabled databases")
    p_bench.add_argument("--skip-load", action="store_true", help="Skip data loading phase")

    # report
    subparsers.add_parser("report", help="Generate publication charts and markdown report")

    # run-all
    subparsers.add_parser("run-all", help="Execute complete automated benchmark pipeline")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch = {
        "validate": cmd_validate,
        "prepare-data": cmd_prepare_data,
        "load": cmd_load,
        "benchmark": cmd_benchmark,
        "report": cmd_report,
        "run-all": cmd_run_all,
    }

    cmd_fn = dispatch.get(args.command)
    if cmd_fn:
        sys.exit(cmd_fn(config, args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
