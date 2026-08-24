# Graph Database Cloud Benchmarking Report

**Generated**: 2026-08-24 18:57:25 UTC

This report presents empirical performance metrics comparing CognDB Cloud, Neo4j, Memgraph, FalkorDB, and Kùzu.

## 1. Data Ingestion Performance

|    | database   |   nodes_loaded |   rels_loaded |   total_load_time_sec |   nodes_per_sec |   rels_per_sec |   total_records_per_sec |
|----|------------|----------------|---------------|-----------------------|-----------------|----------------|-------------------------|
|  0 | kuzu       |          34546 |        421534 |                  0.93 |       200964.39 |     1320676.75 |               492660.11 |


## 2. Workload Latency Metrics (p50, p90, p95, p99, Throughput)

|    | database   | workload        |   successful_operations |   failed_operations |   p50_ms |   p95_ms |   p99_ms |   mean_ms |   throughput_ops_sec |
|----|------------|-----------------|-------------------------|---------------------|----------|----------|----------|-----------|----------------------|
|  0 | kuzu       | aggregation     |                     300 |                   0 |   63.300 |   72.168 |   75.886 |    62.727 |               16.247 |
|  1 | kuzu       | filtered_lookup |                     300 |                   0 |    2.228 |    2.827 |    3.253 |     2.294 |              452.433 |
|  2 | kuzu       | point_lookup    |                     300 |                   0 |    4.953 |    5.626 |    5.828 |     5.031 |              207.727 |
|  3 | kuzu       | traversal_1_hop |                     300 |                   0 |    1.571 |    2.010 |    2.250 |     1.608 |              657.700 |
|  4 | kuzu       | traversal_2_hop |                     300 |                   0 |    6.012 |    9.055 |   10.324 |     6.121 |              170.437 |
|  5 | kuzu       | traversal_3_hop |                     300 |                   0 |   11.904 |   18.275 |   20.440 |    11.934 |               87.950 |


## 3. Concurrent Multi-Client Mixed Read/Write Scaling

|    | database   |   concurrency |   total_operations |   successful_operations |   failed_operations |   throughput_ops_sec |   read_throughput_ops_sec |   write_throughput_ops_sec |   p50_ms |   p95_ms |   error_rate |
|----|------------|---------------|--------------------|-------------------------|---------------------|----------------------|---------------------------|----------------------------|----------|----------|--------------|
|  0 | kuzu       |            10 |              13927 |                   11166 |                2761 |               464.15 |                    372.13 |                      92.02 |    15.65 |    60.46 |         0.20 |
|  1 | kuzu       |            20 |              13922 |                   11053 |                2869 |               463.97 |                    368.35 |                      95.61 |    30.30 |   127.85 |         0.21 |
|  2 | kuzu       |            40 |              13921 |                   11066 |                2855 |               463.86 |                    368.73 |                      95.13 |    51.68 |   275.15 |         0.21 |

