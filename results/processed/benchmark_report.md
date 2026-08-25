# Graph Database Cloud Benchmarking Report

**Generated**: 2026-08-25 19:28:35 UTC

This report presents empirical performance metrics evaluating **CognDB Cloud** alongside **Neo4j**, **Memgraph**, **FalkorDB**, and **Kùzu** under identical workloads and standardized datasets.

## 1. Database Platform Matrix & Status

| Database       | Key      | Deployment Type                    | Hosting                          | vCPU / RAM      | Query Language                     | Status                    |
|----------------|----------|------------------------------------|----------------------------------|-----------------|------------------------------------|---------------------------|
| CognDB Cloud   | cognodb  | Managed Cloud DBaaS                | AWS Managed Cloud                | 1 vCPU / 4.0 GB | Cypher (openCypher / Bolt v4.4+)   | Measured (Live Benchmark) |
| Neo4j AuraDB   | neo4j    | Managed Cloud DBaaS                | GCP / AWS Cloud                  | 1 vCPU / 4.0 GB | Cypher (Cypher 5 / openCypher)     | Measured (Live Benchmark) |
| Memgraph Cloud | memgraph | Managed In-Memory Cloud DBaaS      | AWS Cloud / Container Sandbox    | 1 vCPU / 4.0 GB | openCypher                         | Measured (Live Benchmark) |
| FalkorDB Cloud | falkordb | Managed Redis-Based Graph DBaaS    | AWS Cloud / Redis Module Sandbox | 1 vCPU / 4.0 GB | openCypher                         | Measured (Live Benchmark) |
| Kùzu           | kuzu     | In-Process Columnar Storage Engine | Local / In-Process               | 1 vCPU / 4.0 GB | Cypher (Native OpenCypher dialect) | Measured (Live Benchmark) |


## 2. Data Ingestion Performance

| Database   |   Nodes Ingested |   Edges Ingested |   Total Time (s) |   Nodes / sec |      Rels / sec |   Total Ingestion Rate (records/sec) |
|------------|------------------|------------------|------------------|---------------|-----------------|--------------------------------------|
| COGNODB    |           34,546 |          421,534 |           102.98 |        4652   |  6047           |                               5909   |
| FALKORDB   |           34,546 |          421,534 |            59.16 |       45041.8 |  7224           |                               7714.5 |
| KUZU       |           34,546 |          421,534 |             0.85 |      222312   |     1.61378e+06 |                             539001   |
| MEMGRAPH   |           34,546 |          421,534 |            28.98 |       10072.9 | 16526.5         |                              15757.1 |
| NEO4J      |           34,546 |          405,000 |            54.13 |       11291.9 |  8400           |                               8558.4 |


## 3. Workload Latency Metrics (p50, p90, p95, p99, Throughput)

| Database   | Workload        |   Success Ops |   Failed Ops |   p50 (ms) |   p95 (ms) |   p99 (ms) |   Mean (ms) |   Throughput (ops/s) |
|------------|-----------------|---------------|--------------|------------|------------|------------|-------------|----------------------|
| COGNODB    | aggregation     |           595 |            5 |    4454.73 |    5297.93 |    5842.56 |     4564.14 |                  0.2 |
| COGNODB    | filtered_lookup |           600 |            0 |     280.85 |     324.68 |     370.64 |      280.79 |                  3.6 |
| COGNODB    | point_lookup    |           600 |            0 |     275.61 |     338.74 |     396.16 |      280.02 |                  3.6 |
| COGNODB    | traversal_1_hop |           600 |            0 |     273.67 |     332.71 |     522.16 |      280.15 |                  3.6 |
| COGNODB    | traversal_2_hop |           600 |            0 |     283.43 |     315.52 |     371.58 |      276.83 |                  3.6 |
| COGNODB    | traversal_3_hop |           600 |            0 |     283.41 |     403.61 |     647.83 |      292.81 |                  3.4 |
| FALKORDB   | aggregation     |          1200 |            0 |     594.33 |     650.46 |     678.92 |      585.99 |                  1.7 |
| FALKORDB   | filtered_lookup |          1200 |            0 |      21.58 |      25.86 |      31.39 |       22.32 |                 44.8 |
| FALKORDB   | point_lookup    |          1200 |            0 |      20.97 |      24.69 |      27.37 |       21.67 |                 46.5 |
| FALKORDB   | traversal_1_hop |          1200 |            0 |      21.43 |      23.84 |      47.61 |       22.2  |                 45.8 |
| FALKORDB   | traversal_2_hop |          1200 |            0 |      21.27 |      25.21 |      44.92 |       22.49 |                 45   |
| FALKORDB   | traversal_3_hop |          1200 |            0 |      21.09 |      24.58 |      39.41 |       22.12 |                 45.4 |
| KUZU       | aggregation     |          1500 |            0 |      51.31 |      56.57 |      59.96 |       51.57 |                 19.8 |
| KUZU       | filtered_lookup |          1500 |            0 |       1.94 |       2.5  |       2.8  |        2    |                503   |
| KUZU       | point_lookup    |          1500 |            0 |       4.18 |       4.99 |       5.65 |        4.29 |                236.6 |
| KUZU       | traversal_1_hop |          1500 |            0 |       1.34 |       1.82 |       2.17 |        1.4  |                722.6 |
| KUZU       | traversal_2_hop |          1500 |            0 |       5.02 |       7.64 |       8.57 |        5.17 |                195.2 |
| KUZU       | traversal_3_hop |          1500 |            0 |      10.4  |      15.63 |      17.19 |       10.32 |                 99.6 |
| MEMGRAPH   | aggregation     |          1200 |            0 |     338.91 |     391.25 |     548.51 |      352.47 |                  2.8 |
| MEMGRAPH   | filtered_lookup |          1200 |            0 |     161.83 |     187.45 |     206.71 |      164.4  |                  6.1 |
| MEMGRAPH   | point_lookup    |          1200 |            0 |     163.36 |     180.09 |     201.1  |      163.94 |                  6.2 |
| MEMGRAPH   | traversal_1_hop |          1200 |            0 |     159.75 |     179.39 |     226.66 |      162.44 |                  6.2 |
| MEMGRAPH   | traversal_2_hop |          1200 |            0 |     161.79 |     181.58 |     218.89 |      163.17 |                  6.2 |
| MEMGRAPH   | traversal_3_hop |          1200 |            0 |     163.15 |     185.82 |     322.45 |      165.4  |                  6.1 |
| NEO4J      | aggregation     |           900 |            0 |     198.53 |     247.42 |     345.6  |      206.05 |                  4.9 |
| NEO4J      | filtered_lookup |           900 |            0 |      80.65 |      88    |     120.08 |       83.2  |                 12   |
| NEO4J      | point_lookup    |           900 |            0 |      80.48 |      92.82 |     114.33 |       83.42 |                 12   |
| NEO4J      | traversal_1_hop |           900 |            0 |      78.41 |      93.91 |     128.27 |       81.89 |                 12.2 |
| NEO4J      | traversal_2_hop |           900 |            0 |      74.48 |      88.35 |     126.61 |       78.38 |                 12.9 |
| NEO4J      | traversal_3_hop |           900 |            0 |      74.8  |      88.85 |     121.61 |       77.01 |                 13.1 |


## 4. Concurrent Multi-Client Mixed Read/Write Scaling

| Database   | Concurrency   |   Total Ops |   Success Ops |   Failed Ops |   Total Throughput (ops/s) |   Read Ops/s |   Write Ops/s |   p50 (ms) |   p95 (ms) | Error Rate   |
|------------|---------------|-------------|---------------|--------------|----------------------------|--------------|---------------|------------|------------|--------------|
| COGNODB    | 10 workers    |       1,635 |         1,635 |            0 |                       26.3 |         20.9 |           5.4 |     251.56 |    1547.54 | 0.0%         |
| COGNODB    | 20 workers    |       3,365 |         3,365 |            0 |                       54.1 |         43.1 |          11   |     250.35 |    1566.75 | 0.0%         |
| COGNODB    | 40 workers    |       6,253 |         6,253 |            0 |                       99   |         79.5 |          19.6 |     264.17 |    1650.89 | 0.0%         |
| FALKORDB   | 10 workers    |      47,736 |        47,736 |            0 |                      397.6 |        318.2 |          79.4 |      23.42 |      30.13 | 0.0%         |
| FALKORDB   | 20 workers    |     105,393 |       105,393 |            0 |                      877.7 |        700.4 |         177.3 |      20.94 |      29.25 | 0.0%         |
| FALKORDB   | 40 workers    |     141,523 |       141,523 |            0 |                     1176.3 |        939.2 |         237.2 |      27.26 |      50.77 | 0.0%         |
| KUZU       | 10 workers    |      78,196 |        62,614 |       15,582 |                      521.2 |        417.4 |         103.9 |      12.95 |      59.95 | 19.9%        |
| KUZU       | 20 workers    |      62,002 |        49,198 |       12,804 |                      413.2 |        327.9 |          85.3 |      34.33 |     149.92 | 20.7%        |
| KUZU       | 40 workers    |      56,936 |        45,219 |       11,717 |                      379.4 |        301.3 |          78.1 |      62.44 |     350.47 | 20.6%        |
| MEMGRAPH   | 10 workers    |       7,435 |         7,435 |            0 |                       61.7 |         48.5 |          13.2 |     153.29 |     181.01 | 0.0%         |
| MEMGRAPH   | 20 workers    |      14,826 |        14,826 |            0 |                      122.8 |         96.9 |          25.9 |     154.04 |     182.16 | 0.0%         |
| MEMGRAPH   | 40 workers    |      25,845 |        25,845 |            0 |                      213.8 |        169.9 |          43.9 |     175.7  |     289.12 | 0.0%         |
| NEO4J      | 10 workers    |      10,660 |        10,660 |            0 |                      118.2 |         92.9 |          25.3 |      80.4  |      99.4  | 0.0%         |
| NEO4J      | 20 workers    |      22,854 |        22,854 |            0 |                      253.2 |        200.2 |          53.1 |      78.45 |      91.7  | 0.0%         |
| NEO4J      | 40 workers    |      44,543 |        44,543 |            0 |                      493.5 |        392.3 |         101.2 |      79.2  |      93.25 | 0.0%         |

