# System Architecture

## 1. High-Level Architecture

The benchmarking framework is structured into modular layers adhering to dependency inversion and separation of concerns:

```
                            +-----------------------------------+
                            |         CLI / Entrypoints         |
                            | (benchmark.cli / run_all.py, etc) |
                            +-----------------+-----------------+
                                              |
                            +-----------------v-----------------+
                            |         Benchmark Runner          |
                            +----+------------+------------+----+
                                 |            |            |
         +-----------------------+            |            +-----------------------+
         |                                    |                                    |
+--------v--------+                  +--------v--------+                  +--------v--------+
| Dataset Manager |                  | Workload Engine |                  | Statistics &    |
| (Download, Seed,|                  | (Traversals,    |                  | Timing Engine   |
|  Preprocess,    |                  |  Point/Filtered,|                  | (perf_counter_ns|
|  Validation)    |                  |  Aggregations,  |                  |  NumPy percent) |
+-----------------+                  |  Mixed Concurr) |                  +--------+--------+
                                     +--------+--------+                           |
                                              |                                    |
                                     +--------v--------+                           |
                                     | Adapter Contract|                           |
                                     | (Base Adapter)  |                           |
                                     +--------+--------+                           |
                                              |                                    |
    +-----------------+-----------------+-----+-----------+-----------------+      |
    |                 |                 |                 |                 |      |
+---v----+       +----v---+       +-----v----+      +-----v----+      +-----v----+ |
| CognDB |       |  Neo4j |       | Memgraph |      | FalkorDB |      |   Kùzu   | |
| Cloud  |       | Engine |       | In-Memory|      |  Redis   |      | Columnar | |
| Adapter|       | Adapter|       |  Adapter |      |  Adapter |      | Adapter  | |
+--------+       +--------+       +----------+      +----------+      +----------+ |
                                                                                   |
                                                                          +--------v--------+
                                                                          | Result Storage  |
                                                                          | Raw: .jsonl     |
                                                                          | Processed: .csv |
                                                                          | Charts: .png    |
                                                                          +-----------------+
```

---

## 2. Component Design & Responsibilities

### 2.1 Configuration Layer (`src/benchmark/config.py`)
- Reads YAML definitions (`benchmark.yaml`, `databases.yaml`, `workloads.yaml`).
- Interpolates environment variables securely with `python-dotenv`.
- Supplies typed metadata (`DatabaseMetadata`) and runtime parameters across runner components.

### 2.2 Dataset Subsystem (`src/benchmark/dataset/`)
- `loader.py`: Stream downloads SNAP graph archives with automated gzip extraction and raw edge parsing.
- `generator.py`: Converts raw edge tuples into standardized node and edge tables. Remaps node IDs to dense sequential integers, deterministically assigns categories, publication years, and citation weights using fixed seed (`42`).
- `validator.py`: Verifies node uniqueness, schema conformance, dangling edge elimination, and degree distribution metrics.

### 2.3 Database Adapter Layer (`src/benchmark/adapters/`)
Implements the uniform `GraphDatabaseAdapter` abstract contract:
- `connect()`: Initializes driver pool, sets timeouts, and validates live ping.
- `clear_database()`: Resets graph state to pristine condition.
- `create_schema()`: Enforces primary key unique constraints and secondary indexes.
- `load_data()`: Ingests normalized node and edge batches via optimal driver mechanisms (`UNWIND`, `COPY FROM`).
- `execute_query()`: Executes query and consumes entire result stream into memory to ensure accurate server execution timing.
- `get_resource_usage()`: Gathers CPU/memory snapshots or marks remote DBaaS as `not_observable`.

### 2.4 Workload Engine (`src/benchmark/workloads/`)
- `base.py`: Isolates unmeasured warm-up iterations (default: 20) from measured benchmark iterations (default: 100). Employs `time.perf_counter_ns()` with microsecond accuracy.
- `traversal.py`: Implements 1-hop, 2-hop, and 3-hop neighbor and path traversals with deterministic seed node sequences.
- `lookup.py`: Evaluates primary key point lookups and property-filtered category scans.
- `aggregation.py`: Evaluates grouped relationship aggregation.
- `mixed.py`: Multi-client concurrent execution (10, 20, 40 workers) simulating real-world production load.

### 2.5 Statistical Engine & Visualization (`src/benchmark/statistics.py`, `src/benchmark/reporter.py`)
- Computes true percentiles ($p_{50}, p_{90}, p_{95}, p_{99}$), arithmetic mean, standard deviation, and throughput.
- Persists raw JSONL logs in `results/raw/<database>/<workload>_<run_id>.jsonl` and processed summaries in `results/processed/`.
- Automated Matplotlib generation of publication-quality charts.
