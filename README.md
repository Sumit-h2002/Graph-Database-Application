# Graph Database Cloud Benchmarking Suite

A production-quality, reproducible, and technically defensible benchmarking framework evaluating **CognDB Cloud** alongside **Neo4j**, **Memgraph**, **FalkorDB**, and **Kùzu** under identical logical workloads, normalized datasets, and equivalent resource constraints.

---

## 1. Overview

Graph databases are deployed across diverse access patterns ranging from sub-millisecond point lookups and multi-hop neighborhood traversals to concurrent transactional mutation and large-scale analytical aggregation.

This benchmark suite evaluates:
- **Bulk & Transactional Ingestion Throughput** (Nodes/sec, Relationships/sec)
- **1-Hop, 2-Hop, and 3-Hop Graph Traversal Latencies** ($p_{50}, p_{90}, p_{95}, p_{99}$, Mean, Min, Max)
- **Primary Key Point Lookups** (`:Paper(id)`)
- **Property-Filtered Scans** (`:Paper(category)`)
- **Grouped Analytical Aggregations**
- **Multi-Client Concurrency Scaling** (10, 20, and 40 concurrent worker threads with an 80/20 Read/Write distribution)
- **Resource Utilization & Observability**

---

## 2. Architecture

```
                            +-----------------------------------+
                            |           CLI Interface           |
                            | (python -m benchmark.cli run-all) |
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
| (SNAP cit-HepPh |                  | (1/2/3 Hop,     |                  | Timing Engine   |
|  Normalized CSV |                  |  Lookups, Aggs, |                  | (perf_counter_ns|
|  Seed: 42)      |                  |  Concurrency)   |                  |  NumPy percent) |
+-----------------+                  +--------+--------+                  +--------+--------+
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
                                                                          | Results & Visual|
                                                                          | Raw: .jsonl     |
                                                                          | Processed: .csv |
                                                                          | Charts: .png    |
                                                                          +-----------------+
```

---

## 3. Database Platforms Selected

| Platform | Architectural Model | Rationale for Inclusion | Query Language | Driver |
| :--- | :--- | :--- | :--- | :--- |
| **CognDB Cloud** | Cloud-native Graph DBaaS | Target system under evaluation. Cypher/Bolt protocol compatible. | Cypher | `neo4j>=5.10.0` |
| **Neo4j** | Native Graph Engine (PageCache) | The industry standard reference graph database. | Cypher | `neo4j>=5.10.0` |
| **Memgraph** | In-Memory Graph Database | High-throughput, C++ in-memory architecture with Cypher support. | openCypher | `neo4j>=5.10.0` |
| **FalkorDB** | Redis-Based Low-Latency Graph | Graph engine built on Redis with GraphBLAS matrix multiplication. | openCypher | `falkordb>=1.0.0` / `redis>=8.0` |
| **Kùzu** | Embedded Columnar Graph Engine | State-of-the-art columnar graph engine (the DuckDB of graphs). | Cypher | `kuzu>=0.4.0` |

---

## 4. Dataset Specification

The benchmark uses the recognized **Stanford Network Analysis Platform (SNAP) `cit-HepPh`** citation graph:
- **Domain**: High Energy Physics arXiv paper citations (1992–2003)
- **Source**: `https://snap.stanford.edu/data/cit-HepPh.txt.gz`
- **Node Count**: 34,546 `:Paper` nodes
- **Relationship Count**: 421,578 `:CITES` relationships
- **Properties**:
  - `Paper.id`: `INT64` (Dense unique identifier)
  - `Paper.name`: `STRING` (`Paper_<id>`)
  - `Paper.category`: `STRING` (Standardized research category)
  - `Paper.year`: `INT64` (Publication year)
  - `Paper.weight`: `DOUBLE` (Citation weight)
  - `CITES.weight`: `DOUBLE` (Edge weight)

**Deterministic Seed**: All sampling, partitioning, and fallback synthetic generation use `random_seed: 42`.

---

## 5. Benchmarking Methodology & Fairness

1. **High-Precision Timing**: Latencies are recorded using `time.perf_counter_ns()` with nanosecond precision.
2. **Warm-up Isolation**: Each workload executes **20 warm-up operations** before recording **100 measured operations**. Warm-up iterations are strictly omitted from reported percentiles.
3. **Repetition**: All benchmarks execute across **3 distinct repetitions** with unique run IDs to track variance.
4. **Deterministic Seed Selection**: The starting node IDs for 1-hop, 2-hop, and 3-hop traversals and point lookups are generated identically across all database platforms.
5. **Multi-Client Concurrency**: Evaluates 10, 20, and 40 concurrent client worker threads executing an 80% Read / 20% Write transactional mix for 30 seconds per concurrency level.
6. **No Fabricated Numbers**: If a live cloud database has not been run in a specific test session, its status is documented as `Not yet measured`.

---

## 6. Installation & Quick Start

### Prerequisites
- Python 3.11+ (Python 3.11, 3.12, or 3.13)
- Git

### 1. Clone & Setup Environment
```bash
git clone <repository_url> graph-db-benchmark
cd graph-db-benchmark
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

### 2. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your database endpoints and credentials in `.env` (never commit `.env`).

---

## 7. Execution Commands

### Run Complete End-to-End Benchmark Pipeline
```bash
python -m benchmark.cli run-all
```
This automatically:
1. Validates configuration and schema integrity.
2. Downloads and pre-processes the standardized SNAP dataset.
3. Loads data and creates indexes.
4. Executes all warm-ups and measured workloads across repetitions.
5. Calculates true NumPy percentiles and throughput.
6. Generates high-resolution Matplotlib charts in `results/charts/`.
7. Compiles a Markdown summary report in `results/processed/benchmark_report.md`.

### Run Individual Subcommands
```bash
# Validate environment & config
python -m benchmark.cli validate

# Download & normalize dataset
python -m benchmark.cli prepare-data

# Load data into a single database (e.g. Kùzu, CognDB, Neo4j)
python -m benchmark.cli load --database kuzu

# Benchmark a single database
python -m benchmark.cli benchmark --database kuzu

# Generate charts and markdown report from existing results
python -m benchmark.cli report
```

### Running Test Suite
```bash
python -m pytest -v
```

---

## 8. Benchmark Workloads Reference

| Workload | Logical Operation | Query Pattern |
| :--- | :--- | :--- |
| **Loading** | Bulk & transactional batch ingestion | `UNWIND $batch AS row CREATE (:Paper ...)` / `COPY FROM` |
| **Point Lookup** | Primary key indexed lookup | `MATCH (n:Paper {id: $node_id}) RETURN n.id, n.name, ...` |
| **Filtered Lookup** | Category property index scan | `MATCH (n:Paper) WHERE n.category = $category RETURN count(n)` |
| **1-Hop Traversal** | Direct citation expansion | `MATCH (n:Paper {id: $node_id})-[r:CITES]->(m:Paper) RETURN count(m)` |
| **2-Hop Traversal** | 2nd-degree citation neighborhood | `MATCH (n:Paper {id: $node_id})-[r1]->(m)-[r2]->(k) RETURN count(DISTINCT k)` |
| **3-Hop Traversal** | 3rd-degree deep path expansion | `MATCH (n:Paper {id: $node_id})-[r1]->(m)-[r2]->(k)-[r3]->(p) RETURN count(DISTINCT p)` |
| **Aggregation** | Analytical grouping | `MATCH (n:Paper)-[r:CITES]->(m:Paper) RETURN n.category, count(r)` |
| **Mixed Concurrency**| 10, 20, 40 workers (80% R / 20% W) | Concurrent threads running mixed read queries and node creations |

---

## 9. Project Structure

```
graph-db-benchmark/
├── README.md                 <- Project overview, methodology, and setup guide
├── requirements.txt          <- Project dependencies with official drivers
├── pyproject.toml            <- Build system and pytest configuration
├── .gitignore                <- Secrets, venv, and temporary result exclusions
├── .env.example              <- Template for environment credentials
│
├── config/
│   ├── benchmark.yaml        <- Benchmark iterations, seeds, and paths
│   ├── databases.yaml        <- Platform documentation, specs, and drivers
│   └── workloads.yaml        <- Workload specifications and queries
│
├── data/
│   ├── raw/                  <- Raw downloaded SNAP archives
│   ├── processed/            <- Standardized nodes.csv and edges.csv
│   └── README.md             <- Dataset documentation
│
├── src/
│   └── benchmark/
│       ├── __init__.py
│       ├── cli.py            <- Unified CLI command entrypoint
│       ├── config.py         <- YAML config and environment parser
│       ├── models.py         <- Domain dataclasses and result models
│       ├── runner.py         <- Benchmark orchestration engine
│       ├── statistics.py     <- NumPy percentile and stats calculations
│       ├── reporter.py       <- Automated Matplotlib charts and report
│       ├── logging_config.py <- Secret-masked structured logging
│       │
│       ├── adapters/         <- Unified database adapter layer
│       │   ├── base.py       <- Abstract GraphDatabaseAdapter contract
│       │   ├── cognodb.py    <- CognDB Cloud Bolt adapter
│       │   ├── neo4j.py      <- Neo4j Bolt adapter
│       │   ├── memgraph.py   <- Memgraph Bolt adapter
│       │   ├── falkordb.py   <- FalkorDB Redis adapter
│       │   ├── kuzu.py       <- Kùzu columnar graph adapter
│       │   └── mock.py       <- In-memory mock adapter for tests
│       │
│       ├── dataset/          <- Dataset management
│       │   ├── loader.py     <- SNAP dataset downloader
│       │   ├── generator.py  <- Preprocessing and normalization
│       │   └── validator.py  <- Structural integrity validator
│       │
│       └── workloads/        <- Modular workload definitions
│           ├── base.py       <- Base workload with warmup isolation
│           ├── loading.py    <- Ingestion benchmark
│           ├── traversal.py  <- 1/2/3-hop traversals
│           ├── lookup.py     <- Point and filtered lookups
│           ├── aggregation.py<- Grouped aggregations
│           └── mixed.py      <- Concurrent read/write scaling
│
├── scripts/
│   ├── prepare_dataset.py    <- Standalone dataset preparation script
│   ├── load_database.py      <- Standalone loader script
│   ├── run_benchmark.py      <- Standalone benchmark runner script
│   └── run_all.py            <- Standalone full pipeline script
│
├── tests/                    <- Complete unit test suite
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_dataset.py
│   ├── test_statistics.py
│   ├── test_workloads.py
│   ├── test_adapters.py
│   └── test_runner.py
│
├── results/
│   ├── raw/                  <- Per-iteration raw JSONL logs
│   ├── processed/            <- Aggregated summary CSVs and report
│   └── charts/               <- Generated high-resolution charts
│
└── docs/
    ├── methodology.md        <- Detailed scientific methodology & fairness
    ├── architecture.md       <- System architecture and component details
    └── troubleshooting.md    <- Common setup and operational resolutions
```

---

## 10. Fairness Analysis & Limitations

### 1. Cloud Network Latency vs Embedded Engines
In-process embedded engines like Kùzu execute directly inside the application process without TCP network socket serialization or IPC context switches. Cloud DBaaS instances (such as CognDB Cloud and Neo4j Aura) traverse internet routing and TLS encryption layers. When comparing raw latencies, network Round Trip Time (RTT) must be factored into the architectural analysis.

### 2. Free-Tier Resource Quotas
Public cloud free tiers often restrict concurrent client connection limits, enforce fixed memory caps (e.g. 1GB heap), and throttle sustained high-throughput write bursts.

### 3. Resource Observability
Client database drivers interacting with cloud DBaaS platforms cannot access host-level OS hardware counters (`/proc/stat`, physical RAM consumption). In accordance with benchmark integrity rules, unobservable cloud metrics are marked `not_observable` rather than synthetic approximations.

---

## 11. Reproducibility Guarantee

To reproduce the benchmark results on any workstation:
1. Ensure Python 3.11+ is installed.
2. Run `python -m pytest` to verify contract conformance.
3. Run `python -m benchmark.cli prepare-data` to generate identical normalized graph tables (`random_seed: 42`).
4. Set credentials in `.env` and execute `python -m benchmark.cli benchmark --all`.
