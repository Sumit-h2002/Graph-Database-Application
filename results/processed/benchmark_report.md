# Graph Database Cloud Benchmarking Report

**Generated**: 2026-08-25 11:15:25 UTC

This report presents empirical performance metrics evaluating **CognDB Cloud** alongside **Neo4j**, **Memgraph**, **FalkorDB**, and **Kùzu** under identical workloads and standardized datasets.

## 1. Database Platform Matrix & Status

| Database       | Key      | Deployment Type                    | Hosting                          | vCPU / RAM      | Query Language                     | Status                                          |
|----------------|----------|------------------------------------|----------------------------------|-----------------|------------------------------------|-------------------------------------------------|
| CognDB Cloud   | cognodb  | Managed Cloud DBaaS                | AWS Managed Cloud                | 1 vCPU / 4.0 GB | Cypher (openCypher / Bolt v4.4+)   | Measured (Live Benchmark)                       |
| Neo4j AuraDB   | neo4j    | Managed Cloud DBaaS                | GCP / AWS Cloud                  | 1 vCPU / 4.0 GB | Cypher (Cypher 5 / openCypher)     | Measured (Live Benchmark)                       |
| Memgraph Cloud | memgraph | Managed In-Memory Cloud DBaaS      | AWS Cloud / Container Sandbox    | 1 vCPU / 4.0 GB | openCypher                         | Measured (Live Benchmark)                       |
| FalkorDB Cloud | falkordb | Managed Redis-Based Graph DBaaS    | AWS Cloud / Redis Module Sandbox | 1 vCPU / 4.0 GB | openCypher                         | Not yet measured (Requires credentials in .env) |
| Amazon Neptune | neptune  | Managed Cloud Graph DBaaS          | AWS Cloud (VPC)                  | 2 vCPU / 4.0 GB | openCypher (Bolt v4.4+ over TLS)   | Not yet measured (Requires credentials in .env) |
| Kùzu           | kuzu     | In-Process Columnar Storage Engine | Local / In-Process               | 1 vCPU / 4.0 GB | Cypher (Native OpenCypher dialect) | Measured (Live Benchmark)                       |


## 2. Data Ingestion Performance

| Database       | Nodes Ingested   | Edges Ingested   | Total Time (s)   | Nodes / sec   | Rels / sec   | Total Ingestion Rate (records/sec)   |
|----------------|------------------|------------------|------------------|---------------|--------------|--------------------------------------|
| COGNODB        | 34,546           | 421,534          | 154.52           | 2,032.4       | 3,065.2      | 2,951.6                              |
| KUZU           | 34,546           | 421,534          | 0.88             | 204,113.6     | 1,537,026.4  | 516,877.2                            |
| MEMGRAPH       | 34,546           | 421,534          | 28.64            | 10,617.9      | 16,608.0     | 15,927.0                             |
| NEO4J          | 34,546           | 405,000          | 72.87            | 5,912.5       | 6,042.5      | 6,032.0                              |
| FalkorDB Cloud | -                | -                | Not yet measured | -             | -            | -                                    |
| Amazon Neptune | -                | -                | Not yet measured | -             | -            | -                                    |


## 3. Workload Latency Metrics (p50, p90, p95, p99, Throughput)

| Database       | Workload                                 | Success Ops   | Failed Ops   | p50 (ms)         | p95 (ms)   | p99 (ms)   | Mean (ms)   | Throughput (ops/s)   |
|----------------|------------------------------------------|---------------|--------------|------------------|------------|------------|-------------|----------------------|
| COGNODB        | aggregation                              | 295           | 5            | 4352.30          | 5463.01    | 6142.91    | 4516.03     | 0.2                  |
| COGNODB        | filtered_lookup                          | 300           | 0            | 295.99           | 324.18     | 344.52     | 287.56      | 3.5                  |
| COGNODB        | point_lookup                             | 300           | 0            | 290.25           | 326.29     | 362.52     | 287.34      | 3.5                  |
| COGNODB        | traversal_1_hop                          | 300           | 0            | 297.65           | 311.94     | 328.90     | 284.76      | 3.5                  |
| COGNODB        | traversal_2_hop                          | 300           | 0            | 302.10           | 315.42     | 359.55     | 285.95      | 3.5                  |
| COGNODB        | traversal_3_hop                          | 300           | 0            | 304.94           | 401.78     | 748.40     | 303.94      | 3.3                  |
| KUZU           | aggregation                              | 900           | 0            | 52.94            | 59.11      | 62.64      | 53.13       | 19.2                 |
| KUZU           | filtered_lookup                          | 900           | 0            | 2.02             | 2.64       | 2.99       | 2.09        | 486.5                |
| KUZU           | point_lookup                             | 900           | 0            | 4.44             | 5.18       | 5.62       | 4.52        | 225.0                |
| KUZU           | traversal_1_hop                          | 900           | 0            | 1.41             | 1.93       | 2.24       | 1.47        | 697.8                |
| KUZU           | traversal_2_hop                          | 900           | 0            | 5.25             | 8.03       | 9.08       | 5.40        | 188.0                |
| KUZU           | traversal_3_hop                          | 900           | 0            | 10.56            | 16.01      | 17.57      | 10.53       | 96.8                 |
| MEMGRAPH       | aggregation                              | 600           | 0            | 339.37           | 391.79     | 423.96     | 347.94      | 2.9                  |
| MEMGRAPH       | filtered_lookup                          | 600           | 0            | 152.14           | 165.10     | 173.08     | 153.89      | 6.5                  |
| MEMGRAPH       | point_lookup                             | 600           | 0            | 150.17           | 163.62     | 173.78     | 153.95      | 6.5                  |
| MEMGRAPH       | traversal_1_hop                          | 600           | 0            | 149.31           | 152.51     | 174.05     | 150.43      | 6.6                  |
| MEMGRAPH       | traversal_2_hop                          | 600           | 0            | 150.14           | 159.80     | 195.75     | 153.21      | 6.5                  |
| MEMGRAPH       | traversal_3_hop                          | 600           | 0            | 150.59           | 163.34     | 231.72     | 154.70      | 6.5                  |
| NEO4J          | aggregation                              | 300           | 0            | 199.55           | 243.37     | 408.93     | 208.29      | 4.8                  |
| NEO4J          | filtered_lookup                          | 300           | 0            | 80.58            | 86.98      | 137.15     | 84.02       | 11.9                 |
| NEO4J          | point_lookup                             | 300           | 0            | 80.58            | 94.36      | 122.69     | 83.38       | 12.0                 |
| NEO4J          | traversal_1_hop                          | 300           | 0            | 79.80            | 90.68      | 147.28     | 84.75       | 11.8                 |
| NEO4J          | traversal_2_hop                          | 300           | 0            | 79.99            | 92.88      | 153.81     | 84.71       | 11.8                 |
| NEO4J          | traversal_3_hop                          | 300           | 0            | 63.57            | 87.20      | 111.07     | 66.85       | 15.0                 |
| FalkorDB Cloud | All Workloads (1/2/3-hop, lookups, aggs) | -             | -            | Not yet measured | -          | -          | -           | -                    |
| Amazon Neptune | All Workloads (1/2/3-hop, lookups, aggs) | -             | -            | Not yet measured | -          | -          | -           | -                    |


## 4. Concurrent Multi-Client Mixed Read/Write Scaling

| Database       | Concurrency          | Total Ops   | Success Ops   | Failed Ops   | Total Throughput (ops/s)   | Read Ops/s   | Write Ops/s   | p50 (ms)   | p95 (ms)   | Error Rate   |
|----------------|----------------------|-------------|---------------|--------------|----------------------------|--------------|---------------|------------|------------|--------------|
| COGNODB        | 10 workers           | 1,204       | 1,204         | 0            | 39.8                       | 31.7         | 8.2           | 241.17     | 266.35     | 0.0%         |
| COGNODB        | 20 workers           | 2,481       | 2,481         | 0            | 82.2                       | 65.3         | 16.9          | 235.84     | 259.90     | 0.0%         |
| COGNODB        | 40 workers           | 4,533       | 4,533         | 0            | 149.8                      | 119.7        | 30.1          | 251.79     | 298.43     | 0.0%         |
| KUZU           | 10 workers           | 42,734      | 34,226        | 8,508        | 474.7                      | 380.2        | 94.5          | 13.97      | 64.49      | 19.9%        |
| KUZU           | 20 workers           | 34,477      | 27,353        | 7,124        | 383.0                      | 303.8        | 79.1          | 36.66      | 163.12     | 20.7%        |
| KUZU           | 40 workers           | 31,436      | 24,946        | 6,490        | 349.1                      | 277.0        | 72.1          | 68.33      | 381.04     | 20.7%        |
| MEMGRAPH       | 10 workers           | 3,714       | 3,714         | 0            | 61.6                       | 48.4         | 13.2          | 155.46     | 166.65     | 0.0%         |
| MEMGRAPH       | 20 workers           | 7,215       | 7,215         | 0            | 119.4                      | 94.4         | 25.0          | 157.93     | 187.33     | 0.0%         |
| MEMGRAPH       | 40 workers           | 10,628      | 10,628        | 0            | 175.3                      | 139.7        | 35.6          | 200.92     | 397.50     | 0.0%         |
| NEO4J          | 10 workers           | 3,595       | 3,595         | 0            | 119.6                      | 94.0         | 25.6          | 79.91      | 90.04      | 0.0%         |
| NEO4J          | 20 workers           | 8,133       | 8,133         | 0            | 270.4                      | 213.8        | 56.6          | 77.40      | 89.19      | 0.0%         |
| NEO4J          | 40 workers           | 14,562      | 14,562        | 0            | 484.1                      | 385.0        | 99.1          | 79.34      | 91.21      | 0.0%         |
| FalkorDB Cloud | 10 / 20 / 40 workers | -           | -             | -            | Not yet measured           | -            | -             | -          | -          | -            |
| Amazon Neptune | 10 / 20 / 40 workers | -           | -             | -            | Not yet measured           | -            | -             | -          | -          | -            |

