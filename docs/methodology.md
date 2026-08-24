# Benchmark Methodology & Fairness Analysis

## 1. Executive Summary

This benchmarking framework provides an empirical, fair, and reproducible performance evaluation of **CognDB Cloud** alongside four representative graph database platforms: **Neo4j**, **Memgraph**, **FalkorDB**, and **Kùzu**.

The benchmark framework enforces strict methodological rigor:
- **No Fabricated Data**: Measurements reflect only actual executed benchmarks. Unmeasured environments are explicitly reported as `Not yet measured`.
- **Identical Datasets**: Every database receives the exact same normalized node and edge records generated from public SNAP data using fixed seed `random_seed: 42`.
- **Identical Logical Workloads**: Workloads test equivalent graph queries (1-hop, 2-hop, 3-hop traversals, primary key lookups, category filters, analytical aggregations, and concurrent read/write stress).
- **High-Precision Timing**: Latency is captured with nanosecond precision using Python's `time.perf_counter_ns()`.
- **Cache Isolation**: 20 unmeasured warm-up iterations precede 100 measured iterations for every workload.
- **Statistical Rigor**: Reports median ($p_{50}$), tail ($p_{90}, p_{95}, p_{99}$), arithmetic mean, standard deviation, and throughput (ops/sec).

---

## 2. Platform Profiles & Resource Equivalence

To ensure fair comparison, target environments are standardized on equivalent hardware profiles:

| Database | Version | Architecture / Deployment | Hosting | Target vCPU | Target RAM | Storage | Query Language | Official Driver |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CognDB Cloud** | Cloud v1.x | Managed DBaaS | Cloud (us-east-1) | 2 vCPU | 4.0 GB | 20.0 GB NVMe | Cypher (Bolt) | `neo4j>=5.10.0` |
| **Neo4j** | 5.19.0 | AuraDB Cloud / Self-Hosted Docker | Cloud / Local | 2 vCPU | 4.0 GB | 20.0 GB NVMe | Cypher | `neo4j>=5.10.0` |
| **Memgraph** | 2.15.0 | In-Memory Graph Database | Self-Hosted Docker | 2 vCPU | 4.0 GB | 20.0 GB NVMe | openCypher | `neo4j>=5.10.0` |
| **FalkorDB** | 0.4.0 | Redis-Based Graph Engine | Self-Hosted Docker | 2 vCPU | 4.0 GB | 20.0 GB NVMe | openCypher | `falkordb>=1.0.0` / `redis>=5.0.0` |
| **Kùzu** | 0.4.1 | Columnar Disk Graph Engine | Embedded / Local | 2 vCPU | 4.0 GB | 20.0 GB NVMe | Cypher | `kuzu>=0.4.0` |

### Fairness Disclosures & Architectural Differences
1. **In-Memory vs Disk-Backed**: Memgraph operates primarily in-memory, whereas Neo4j and Kùzu use disk-backed buffer pool page caches. FalkorDB operates within Redis memory with optional persistence.
2. **Network Protocol vs Embedded**: CognDB, Neo4j, and Memgraph communicate over TCP Bolt protocol. FalkorDB communicates over the Redis protocol. Kùzu runs embedded in-process, eliminating TCP socket roundtrip overhead. These architectural characteristics are highlighted in the final analysis.
3. **Cloud Resource Observability**: Cloud DBaaS endpoints do not expose direct OS hardware counters to client drivers. For remote cloud endpoints, resource metrics are marked as `not_observable` rather than inventing synthetic hardware readings.

---

## 3. Dataset & Schema Specification

The benchmark standardizes on the **SNAP `cit-HepPh`** (High Energy Physics citation graph from arXiv):
- **Node Entity**: `:Paper` (34,546 nodes)
  - `id`: `INT64` (Unique primary key)
  - `name`: `STRING` (`Paper_<id>`)
  - `category`: `STRING` (One of 8 theoretical physics categories)
  - `year`: `INT64` (Publication year between 1992 and 2003)
  - `weight`: `DOUBLE` (Citation confidence weight between 0.1 and 1.0)
- **Relationship Entity**: `:CITES` (421,578 relationships)
  - `source_id`: `INT64` (Citing Paper ID)
  - `target_id`: `INT64` (Cited Paper ID)
  - `weight`: `DOUBLE` (Citation strength)

### Indexing Equivalence
Every adapter establishes equivalent primary key unique constraints and secondary property indexes prior to measurement:
- Primary key index on `(:Paper.id)`
- Range/Hash index on `(:Paper.category)`

---

## 4. Workload Definitions & Measurement

### A. Data Loading Benchmark
Measures bulk ingestion throughput:
$$\text{Throughput}_{\text{nodes}} = \frac{\text{Total Nodes Ingested}}{\text{Node Ingestion Time (s)}}$$
$$\text{Throughput}_{\text{rels}} = \frac{\text{Total Relationships Ingested}}{\text{Relationship Ingestion Time (s)}}$$

### B. Graph Traversal Workloads
- **1-Hop Traversal**: Measures direct citation lookup:
  ```cypher
  MATCH (n:Paper {id: $node_id})-[r:CITES]->(m:Paper) RETURN count(m) AS neighbor_count
  ```
- **2-Hop Traversal**: Measures 2nd-degree citation expansion:
  ```cypher
  MATCH (n:Paper {id: $node_id})-[r1:CITES]->(m:Paper)-[r2:CITES]->(k:Paper) RETURN count(DISTINCT k) AS two_hop_count
  ```
- **3-Hop Traversal**: Measures 3rd-degree deep path expansion:
  ```cypher
  MATCH (n:Paper {id: $node_id})-[r1:CITES]->(m:Paper)-[r2:CITES]->(k:Paper)-[r3:CITES]->(p:Paper) RETURN count(DISTINCT p) AS three_hop_count
  ```

### C. Point & Filtered Lookups
- **Point Lookup (ID)**:
  ```cypher
  MATCH (n:Paper {id: $node_id}) RETURN n.id AS id, n.name AS name, n.category AS category, n.year AS year
  ```
- **Filtered Lookup (Category)**:
  ```cypher
  MATCH (n:Paper) WHERE n.category = $category RETURN count(n) AS match_count
  ```

### D. Analytical Aggregation
- **Grouped Category Count**:
  ```cypher
  MATCH (n:Paper)-[r:CITES]->(m:Paper) RETURN n.category AS category, count(r) AS citation_count ORDER BY citation_count DESC LIMIT 20
  ```

### E. Concurrent Mixed Read/Write Scaling
Evaluates system behavior under 10, 20, and 40 concurrent client worker threads:
- **Workload Mix**: 80% Read (Neighbor lookup) / 20% Write (Paper entity creation)
- **Duration**: 30 seconds sustained per concurrency tier
- **Metrics**: Total Operations, Successful Ops, Failed Ops, Throughput (ops/sec), Error Rate, $p_{50}$, $p_{95}$, $p_{99}$ Latencies.

---

## 5. Statistical Rigor & Latency Calculation

1. **Timer**: Measurements use `time.perf_counter_ns()`. Millisecond conversion:
   $$\text{latency}_{\text{ms}} = \frac{t_{\text{end}} - t_{\text{start}}}{1{,}000{,}000}$$
2. **Percentiles**: Computed using NumPy over raw unbinned observations:
   $$p_k = \text{np.percentile}(\text{latencies}, k)$$
3. **Warm-up Isolation**: 20 warm-up operations per workload are recorded separately and strictly omitted from all final latency statistics and percentile calculations.
4. **Repetitions**: Benchmarks run for 3 repetitions with unique run IDs to capture inter-run variance.
