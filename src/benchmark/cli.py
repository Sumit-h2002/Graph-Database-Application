"""
Command Line Interface (CLI) for Graph Database Benchmarking Suite.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import List

from benchmark.config import BenchmarkConfig
from benchmark.dataset import DatasetDownloader, GraphGenerator, DatasetValidator
from benchmark.logging_config import setup_logging
from benchmark.reporter import BenchmarkReporter
from benchmark.runner import BenchmarkRunner

logger = logging.getLogger("benchmark.cli")


def cmd_validate(config: BenchmarkConfig, args: argparse.Namespace) -> int:
    """Validates configuration files, dataset files, and environment settings."""
    logger.info("Starting comprehensive benchmark pre-flight validation...")
    errors: List[str] = []

    # 1. Check configs
    if not (config.config_dir / "benchmark.yaml").exists():
        errors.append("Missing benchmark.yaml")
    if not (config.config_dir / "databases.yaml").exists():
        errors.append("Missing databases.yaml")
    if not (config.config_dir / "workloads.yaml").exists():
        errors.append("Missing workloads.yaml")

    # 2. Check dataset
    nodes_file = config.processed_dataset_dir / "nodes.csv"
    edges_file = config.processed_dataset_dir / "edges.csv"

    if not nodes_file.exists() or not edges_file.exists():
        logger.warning("Processed dataset files not found. Auto-generating standardized dataset...")
        gen = GraphGenerator(
            output_dir=config.processed_dataset_dir,
            random_seed=config.benchmark_raw.get("dataset", {}).get("random_seed", 42)
        )
        gen.process_and_save()

    # 3. Validate dataset integrity
    import pandas as pd
    try:
        nodes_df = pd.read_csv(nodes_file)
        edges_df = pd.read_csv(edges_file)
        validator = DatasetValidator(
            min_relationships=config.benchmark_raw.get("dataset", {}).get("min_relationships", 100000),
            max_relationships=config.benchmark_raw.get("dataset", {}).get("max_relationships", 500000)
        )
        report = validator.validate(nodes_df, edges_df, strict_range=False)
        if not report.is_valid:
            errors.extend(report.errors)
        else:
            logger.info(f"Dataset validation passed ({report.node_count:,} nodes, {report.edge_count:,} edges).")
    except Exception as e:
        errors.append(f"Failed to read/validate dataset: {e}")

    if errors:
        for err in errors:
            logger.error(f"[VALIDATION FAILED] {err}")
        return 1

    logger.info("[VALIDATION PASSED] All pre-flight checks succeeded.")
    return 0


def cmd_check_connections(config: BenchmarkConfig, args: argparse.Namespace) -> int:
    """Verifies live network connectivity and authentication for configured databases."""
    import time
    from benchmark.adapters import get_adapter

    target_db = getattr(args, "database", None)
    dbs = config.get_database_configs()
    if target_db:
        target_db = target_db.lower()
        if target_db not in dbs:
            logger.error(f"Unknown database key: '{target_db}'. Available: {list(dbs.keys())}")
            return 1
        dbs = {target_db: dbs[target_db]}

    print("\n" + "=" * 80)
    print("GRAPH DATABASE LIVE CONNECTION & CREDENTIAL VERIFICATION")
    print("=" * 80)

    all_passed = True
    for db_key, meta in dbs.items():
        if db_key == "mock":
            continue
        try:
            adapter = get_adapter(db_key, meta)
            start_ping = time.perf_counter()
            adapter.connect()
            ping_ok = adapter.health_check()
            ping_ms = (time.perf_counter() - start_ping) * 1000
            adapter.close()

            if ping_ok:
                print(f"[+] {meta.name:<20}: [CONNECTED & AUTHENTICATED] (Ping: {ping_ms:.1f}ms)")
            else:
                print(f"[-] {meta.name:<20}: [PING FAILED - UNRESPONSIVE]")
                all_passed = False
        except ValueError as ve:
            print(f"[-] {meta.name:<20}: [MISSING CREDENTIALS] {ve}")
            all_passed = False
        except Exception as e:
            print(f"[X] {meta.name:<20}: [CONNECTION / AUTH FAILED] {e}")
            all_passed = False

    print("=" * 80 + "\n")
    return 0 if all_passed else 1


def cmd_prepare_data(config: BenchmarkConfig, args: argparse.Namespace) -> int:
    """Downloads or generates the standardized graph dataset."""
    logger.info("Preparing standardized benchmark dataset...")
    generator = GraphGenerator(
        output_dir=config.processed_dataset_dir,
        random_seed=config.benchmark_raw.get("dataset", {}).get("random_seed", 42)
    )

    raw_edges = None
    if not getattr(args, "synthetic_only", False):
        loader = DatasetDownloader(
            data_dir=config.raw_dataset_dir,
            dataset_name=config.benchmark_raw.get("dataset", {}).get("name", "cit-HepPh")
        )
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
    db_arg = getattr(args, "database", None)
    if not db_arg or db_arg.lower() == "all":
        dbs = config.get_database_configs()
        target_dbs = [k for k, v in dbs.items() if v.enabled]
    else:
        target_dbs = [db_arg.lower()]

    nodes_df, edges_df, _ = runner.load_dataset()
    from benchmark.adapters import get_adapter

    for db_key in target_dbs:
        db_meta = config.get_database_config(db_key)
        if not db_meta:
            logger.error(f"Unknown database: {db_key}")
            continue

        adapter = get_adapter(db_key, db_meta)
        try:
            adapter.connect()
            adapter.clear_database()
            adapter.create_schema()
            from benchmark.workloads.loading import LoadingWorkload
            loader = LoadingWorkload(batch_size=config.default_batch_size)
            res = loader.run(adapter, nodes_df, edges_df, run_id="manual_load")
            runner.result_store.save_load_results([res])
            logger.info(f"Loaded {db_key}: {res.nodes_loaded:,} nodes, {res.rels_loaded:,} edges in {res.total_load_time_sec:.2f}s")
        except Exception as e:
            logger.error(f"Failed to load data into '{db_key}': {e}")
        finally:
            adapter.close()

    return 0


def cmd_benchmark(config: BenchmarkConfig, args: argparse.Namespace) -> int:
    """Runs benchmark workloads against specified database or all enabled databases."""
    runner = BenchmarkRunner(config)
    target_dbs = []

    db_arg = getattr(args, "database", None)
    if getattr(args, "all", False) or not db_arg or db_arg.lower() == "all":
        dbs = config.get_database_configs()
        target_dbs = [k for k, v in dbs.items() if v.enabled]
    else:
        target_dbs = [db_arg.lower()]

    logger.info(f"Target benchmark databases: {', '.join(target_dbs)}")

    for db_key in target_dbs:
        try:
            runner.run_database_benchmark(db_key=db_key, skip_load=getattr(args, "skip_load", False))
        except Exception as e:
            logger.error(f"Benchmark failed for database '{db_key}': {e}")

    # Automatically generate reports after benchmark execution
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
    p_code = cmd_prepare_data(config, args)
    if p_code != 0:
        return p_code

    # 3. Benchmark All Databases
    args.all = True
    args.database = "all"
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

    # check-connections
    p_check = subparsers.add_parser("check-connections", help="Test live network connectivity and authentication for databases in .env")
    p_check.add_argument("--database", help="Optional specific database key to verify (e.g. cognodb, neo4j, memgraph, falkordb, kuzu)")

    # prepare-data
    p_data = subparsers.add_parser("prepare-data", help="Download and prepare standardized dataset")
    p_data.add_argument("--synthetic-only", action="store_true", help="Force synthetic deterministic generation without download")

    # load
    p_load = subparsers.add_parser("load", help="Load dataset into database(s)")
    p_load.add_argument("--database", help="Target database key (default: all enabled)")

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run benchmark suite")
    p_bench.add_argument("--database", help="Target database key (e.g. cognodb, neo4j, memgraph, falkordb, kuzu, mock, all)")
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
        "check-connections": cmd_check_connections,
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
