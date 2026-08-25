# Graph Database Cloud Benchmarking Report

**Generated**: 2026-08-25 07:32:14 UTC

This report presents empirical performance metrics evaluating **CognDB Cloud** alongside **Neo4j**, **Memgraph**, **FalkorDB**, and **Kùzu** under identical workloads and standardized datasets.

## 1. Database Platform Matrix & Status

| Database     | Key      | Deployment Type                         | Hosting           | vCPU / RAM      | Query Language                     | Status                                          |
|--------------|----------|-----------------------------------------|-------------------|-----------------|------------------------------------|-------------------------------------------------|
| CognDB Cloud | cognodb  | Managed Cloud DBaaS                     | cloud             | 2 vCPU / 4.0 GB | Cypher (openCypher / Bolt v4.4+)   | Not yet measured (Requires credentials in .env) |
| Neo4j        | neo4j    | Self-hosted Docker / AuraDB Cloud       | self-hosted/cloud | 2 vCPU / 4.0 GB | Cypher (Cypher 5 / openCypher)     | Not yet measured (Requires credentials in .env) |
| Memgraph     | memgraph | Self-hosted Docker / Cloud              | self-hosted       | 2 vCPU / 4.0 GB | openCypher                         | Not yet measured (Requires credentials in .env) |
| FalkorDB     | falkordb | Self-hosted Docker / Redis Module       | self-hosted       | 2 vCPU / 4.0 GB | openCypher                         | Not yet measured (Requires credentials in .env) |
| Kùzu         | kuzu     | Embedded Columnar Graph Database Engine | local/embedded    | 2 vCPU / 4.0 GB | Cypher (Native OpenCypher dialect) | Measured (Live Benchmark)                       |


## 2. Data Ingestion Performance

| Database     | Nodes Ingested   | Edges Ingested   | Total Time (s)   | Nodes / sec   | Rels / sec   | Total Ingestion Rate (records/sec)   |
|--------------|------------------|------------------|------------------|---------------|--------------|--------------------------------------|
| KUZU         | 34,546           | 421,534          | 0.88             | 204,113.6     | 1,537,026.4  | 516,877.2                            |
| CognDB Cloud | -                | -                | Not yet measured | -             | -            | -                                    |
| Neo4j        | -                | -                | Not yet measured | -             | -            | -                                    |
| Memgraph     | -                | -                | Not yet measured | -             | -            | -                                    |
| FalkorDB     | -                | -                | Not yet measured | -             | -            | -                                    |


## 3. Workload Latency Metrics (p50, p90, p95, p99, Throughput)

| Database     | Workload                                 | Success Ops   | Failed Ops   | p50 (ms)         | p95 (ms)   | p99 (ms)   | Mean (ms)   | Throughput (ops/s)   |
|--------------|------------------------------------------|---------------|--------------|------------------|------------|------------|-------------|----------------------|
| KUZU         | aggregation                              | 900           | 0            | 52.94            | 59.11      | 62.64      | 53.13       | 19.2                 |
| KUZU         | filtered_lookup                          | 900           | 0            | 2.02             | 2.64       | 2.99       | 2.09        | 486.5                |
| KUZU         | point_lookup                             | 900           | 0            | 4.44             | 5.18       | 5.62       | 4.52        | 225.0                |
| KUZU         | traversal_1_hop                          | 900           | 0            | 1.41             | 1.93       | 2.24       | 1.47        | 697.8                |
| KUZU         | traversal_2_hop                          | 900           | 0            | 5.25             | 8.03       | 9.08       | 5.40        | 188.0                |
| KUZU         | traversal_3_hop                          | 900           | 0            | 10.56            | 16.01      | 17.57      | 10.53       | 96.8                 |
| CognDB Cloud | All Workloads (1/2/3-hop, lookups, aggs) | -             | -            | Not yet measured | -          | -          | -           | -                    |
| Neo4j        | All Workloads (1/2/3-hop, lookups, aggs) | -             | -            | Not yet measured | -          | -          | -           | -                    |
| Memgraph     | All Workloads (1/2/3-hop, lookups, aggs) | -             | -            | Not yet measured | -          | -          | -           | -                    |
| FalkorDB     | All Workloads (1/2/3-hop, lookups, aggs) | -             | -            | Not yet measured | -          | -          | -           | -                    |


## 4. Concurrent Multi-Client Mixed Read/Write Scaling

| Database     | Concurrency          | Total Ops   | Success Ops   | Failed Ops   | Total Throughput (ops/s)   | Read Ops/s   | Write Ops/s   | p50 (ms)   | p95 (ms)   | Error Rate   |
|--------------|----------------------|-------------|---------------|--------------|----------------------------|--------------|---------------|------------|------------|--------------|
| KUZU         | 10 workers           | 42,734      | 34,226        | 8,508        | 474.7                      | 380.2        | 94.5          | 13.97      | 64.49      | 19.9%        |
| KUZU         | 20 workers           | 34,477      | 27,353        | 7,124        | 383.0                      | 303.8        | 79.1          | 36.66      | 163.12     | 20.7%        |
| KUZU         | 40 workers           | 31,436      | 24,946        | 6,490        | 349.1                      | 277.0        | 72.1          | 68.33      | 381.04     | 20.7%        |
| CognDB Cloud | 10 / 20 / 40 workers | -           | -             | -            | Not yet measured           | -            | -             | -          | -          | -            |
| Neo4j        | 10 / 20 / 40 workers | -           | -             | -            | Not yet measured           | -            | -             | -          | -          | -            |
| Memgraph     | 10 / 20 / 40 workers | -           | -             | -            | Not yet measured           | -            | -             | -          | -          | -            |
| FalkorDB     | 10 / 20 / 40 workers | -           | -             | -            | Not yet measured           | -            | -             | -          | -          | -            |

