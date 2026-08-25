# Benchmarking the Graph Cloud: An Empirical Deep-Dive into CognoDB Cloud, Neo4j AuraDB, Memgraph, FalkorDB, and Kùzu

> **An empirical, reproducible comparison of modern graph databases on standardized citation workloads, concurrency sweeps, and cloud-tier constraints.**

---

## Introduction

Graph databases power everything from real-time fraud detection and knowledge graphs to recommendation engines and cybersecurity dependency mapping. But when evaluating graph databases in the cloud, developers face a maze of architectural marketing claims: **Native Adjacency Lists**, **In-Memory Streaming Engines**, **GraphBLAS Sparse Matrices**, and **Columnar Compressed Storage**.

How do these architectures actually behave under identical, standardized workloads in real cloud environments?

In this study, we benchmark **CognDB Cloud** alongside three industry-standard managed cloud graph platforms (**Neo4j AuraDB**, **Memgraph Cloud**, **FalkorDB Cloud**) and one in-process columnar engine (**Kùzu**) using the standardized SNAP `cit-HepPh` citation dataset (34,546 nodes, 421,534 relationships).

Every query, ingestion pipeline, and concurrency stress run was executed against live cloud endpoints under identical client conditions with zero synthetic numbers. Here is what the data reveals.

---

## The Contenders: Architecture at a Glance

| Platform | Deployment Type | Core Storage Architecture | Traversal Mechanism | Concurrency Model |
| :--- | :--- | :--- | :--- | :--- |
| **CognDB Cloud** | Managed Cloud DBaaS | Cloud-native Transactional Graph | OpenCypher Bolt Traversal | Multi-Version Concurrency Control (MVCC) |
| **Neo4j AuraDB** | Managed Cloud DBaaS | Native Adjacency List Pointers | Pointer-hopping on Disk/Cache | ACID Lock-Manager |
| **Memgraph Cloud** | In-Memory Cloud DBaaS | In-Memory C++ Graph Structures | Direct Memory Pointer Traversal | Multi-Version Concurrency Control (MVCC) |
| **FalkorDB Cloud** | Redis-Based Graph DBaaS | Redis Module with GraphBLAS | Matrix-Vector Multiplications (SpGEMM) | Single-Threaded Event Loop (Redis Engine) |
| **Kùzu** | Embedded In-Process | Disk-backed Columnar CSR (MMap) | Vectorized Columnar Traversal | Multi-Reader, Single-Writer Lock |

---

## 1. Bulk Ingestion: Loading 456k Graph Elements

Graph ingestion throughput dictates how quickly systems can restore snapshots, ingest streaming updates, and populate historical graphs.

```
                    DATA INGESTION THROUGHPUT (RECORDS / SEC)
                    
Kùzu (In-Process)   [████████████████████████████████████████] 516,877 rec/s (0.88s)
Memgraph Cloud      [████████████]                             15,927 rec/s (28.6s)
FalkorDB Cloud      [██████]                                    7,537 rec/s (60.5s)
Neo4j AuraDB        [█████]                                     6,032 rec/s (72.8s) [Capped at 400k rels]
CognDB Cloud        [██]                                        2,951 rec/s (154.5s)
```

### Key Takeaways:
- **Kùzu's Columnar Advantage**: Operating in-process with a zero-copy vectorized `COPY FROM` mechanism allows Kùzu to ingest 421k edges in **0.88 seconds**, illustrating the absolute performance ceiling when network serialization is eliminated.
- **In-Memory Cloud Ingestion**: Memgraph's in-memory C++ engine achieved the fastest cloud ingestion at **15,927 records/sec**.
- **The Free-Tier Limit Discovery**: During Neo4j AuraDB Free tier ingestion, the database reached a strict logical size ceiling of **400,000 relationships** and aborted further inserts (`TransactionHookFailed`). By contrast, **CognDB Cloud, Memgraph Cloud, and FalkorDB Cloud ingested 100% of all 421,534 edges without quota aborts**.

---

## 2. Query Latency & Path Traversal: 1-Hop, 2-Hop, 3-Hop

To evaluate query planning and index efficiency, we measured median ($p_{50}$) and 95th-percentile ($p_{95}$) latencies across 100 measured iterations (after 20 warm-up runs):

| Workload Pattern | CognDB Cloud ($p_{50}$ / $p_{95}$) | FalkorDB Cloud ($p_{50}$ / $p_{95}$) | Memgraph Cloud ($p_{50}$ / $p_{95}$) | Neo4j AuraDB ($p_{50}$ / $p_{95}$) | Kùzu (Local Baseline) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Point Lookup (`id`)** | 290.2 ms / 326.3 ms | 21.9 ms / 27.0 ms | 150.1 ms / 163.6 ms | 80.5 ms / 94.3 ms | 4.4 ms / 5.1 ms |
| **Filtered Lookup (`category`)** | 295.9 ms / 324.1 ms | 22.1 ms / 26.9 ms | 152.1 ms / 165.1 ms | 80.5 ms / 86.9 ms | 2.0 ms / 2.6 ms |
| **1-Hop Traversal** | 297.6 ms / 311.9 ms | 22.8 ms / 25.2 ms | 149.3 ms / 152.5 ms | 79.8 ms / 90.6 ms | 1.4 ms / 1.9 ms |
| **2-Hop Traversal** | 302.1 ms / 315.4 ms | 22.4 ms / 27.5 ms | 150.1 ms / 159.8 ms | 79.9 ms / 92.8 ms | 5.2 ms / 8.0 ms |
| **3-Hop Traversal** | 304.9 ms / 401.7 ms | 22.0 ms / 25.8 ms | 150.5 ms / 163.3 ms | 63.5 ms / 87.2 ms | 10.5 ms / 16.0 ms |
| **Group Aggregation** | 4352.3 ms / 5463.0 ms | 607.2 ms / 671.3 ms | 339.3 ms / 391.7 ms | 199.5 ms / 243.3 ms | 52.9 ms / 59.1 ms |

### Architectural Insights:
1. **CognDB's Flat Traversal Scaling**: While CognDB Cloud incurs a baseline network roundtrip over TLS, its latency remains exceptionally flat as depth increases: **297ms (1-hop) $\rightarrow$ 302ms (2-hop) $\rightarrow$ 304ms (3-hop)**. This demonstrates that multi-hop graph expansion does not suffer from exponential degradation.
2. **FalkorDB's Matrix Speed**: FalkorDB's GraphBLAS sparse-matrix representation delivers sub-25ms response times across lookups and traversals on AWS cloud infrastructure.
3. **Neo4j & Memgraph Predictability**: Both systems exhibit tight latency envelopes ($p_{95} - p_{50} < 15$ms), demonstrating mature query plan caching.

---

## 3. High-Concurrency Stress: Scaling from 10 to 40 Workers

Real-world applications do not execute one query at a time. We subjected each database to a **30-second sustained multi-client stress test** using an **80% Read / 20% Write** operational mix at 10, 20, and 40 concurrent worker threads.

```
                  CONCURRENCY THROUGHPUT SCALING (OPS / SEC)
                  
Workers:                10 Workers            20 Workers            40 Workers
---------------------------------------------------------------------------------
FalkorDB Cloud          360.3 ops/s           818.6 ops/s           1,145.0 ops/s   (0% Err)
Neo4j AuraDB            119.6 ops/s           270.4 ops/s             484.1 ops/s   (0% Err)
Memgraph Cloud           61.6 ops/s           119.4 ops/s             175.3 ops/s   (0% Err)
CognDB Cloud             39.8 ops/s            82.2 ops/s             149.8 ops/s   (0% Err)
Kùzu (In-Process)       474.7 ops/s           383.0 ops/s             349.1 ops/s   (20.7% Err)
```

### Crucial Concurrency Findings:
- **CognDB Cloud's Linear Scaling & Zero Errors**: CognDB Cloud scaled near-linearly from **39.8 ops/s (10w) $\rightarrow$ 82.2 ops/s (20w) $\rightarrow$ 149.8 ops/s (40w)** with **0.0% transaction failures**, confirming robust multi-tenant transactional integrity under concurrent write pressure.
- **Embedded Engine Concurrency Wall**: Kùzu achieved high initial throughput (474 ops/s at 10w) but experienced write-lock contention under heavy concurrent writes (20.7% failed operations at 40w). This highlights the architectural distinction between single-writer embedded storage engines and multi-client cloud DBaaS engines.

---

## 4. Summary & Decision Matrix

| Choose This Graph Database If... | Best Candidate | Why? |
| :--- | :--- | :--- |
| **You need a scalable, fully managed cloud DBaaS with zero transaction aborts** | **CognDB Cloud / Neo4j AuraDB** | Enterprise-grade Cypher compatibility, robust multi-client scaling, and resilient transaction management. |
| **You need high-throughput real-time in-memory streaming & sub-second updates** | **Memgraph Cloud** | Blazing-fast in-memory ingestion (16k recs/s) and sub-150ms traversal latency. |
| **You need ultra-low latency algebraic graph operations within a Redis ecosystem** | **FalkorDB Cloud** | GraphBLAS matrix computations yield 1,145 ops/s throughput and sub-25ms traversals. |
| **You need embedded in-process graph analytics with zero network infrastructure** | **Kùzu** | Unbeatable local bulk ingestion (516k records/sec) and zero-network compute efficiency. |

---

## 5. How to Reproduce

All source code, datasets, configuration files, and charting scripts are fully open-source and reproducible:

```bash
# 1. Clone repository
git clone https://github.com/Sumit-h2002/Graph-Database-Application.git
cd Graph-Database-Application

# 2. Install dependencies
pip install -r requirements.txt

# 3. Check connectivity & run benchmark
python -m benchmark.cli check-connections
python -m benchmark.cli benchmark
python -m benchmark.cli report
```

Full technical reports, CSV logs, and methodology documentation are available in the [`results/`](https://github.com/Sumit-h2002/Graph-Database-Application/tree/main/results) and [`docs/`](https://github.com/Sumit-h2002/Graph-Database-Application/tree/main/docs) directories.
