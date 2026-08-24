# Troubleshooting & Operational Guide

## 1. Environment & Connectivity Issues

### 1.1 Bolt Connection Refused or Timeout (CognDB, Neo4j, Memgraph)
- **Symptom**: `ServiceUnavailable: Defunct connection...` or `ConnectionRefusedError`.
- **Resolution**:
  1. Verify the database container or cloud instance is reachable:
     ```bash
     curl -v telnet://<host>:<port>
     ```
  2. Ensure `.env` contains valid credentials (`COGNODB_URI`, `NEO4J_URI`, `MEMGRAPH_URI`).
  3. For Neo4j Aura or CognDB Cloud, verify TLS encryption is configured properly (`COGNODB_ENCRYPTED=true` or `bolt+s://` protocol prefix).

### 1.2 FalkorDB / Redis Connection Error
- **Symptom**: `redis.exceptions.ConnectionError: Error 10061 connecting to localhost:6379`.
- **Resolution**:
  1. Ensure the FalkorDB Docker container is running:
     ```bash
     docker run -p 6379:6379 -it --rm falkordb/falkordb:latest
     ```
  2. Verify graph name configuration in `config/databases.yaml` or `FALKORDB_GRAPH_NAME`.

### 1.3 Kùzu Lock or File Access Issues
- **Symptom**: `RuntimeError: Failed to lock database directory`.
- **Resolution**:
  1. Ensure no other active Python process is accessing the database path (`data/kuzu_db`).
  2. For concurrent benchmarking, Kùzu allows multiple concurrent read transactions, but single-writer concurrency requires transactional serialization.

---

## 2. Resource & Quota Limitations

### 2.1 Free-Tier Cloud DBaaS Limits (Neo4j Aura / CognDB Cloud)
- **Limit**: Free instances may cap memory (e.g. 1GB heap) or enforce maximum node/relationship quotas (e.g. 200,000 nodes / 400,000 relationships).
- **Resolution**: The benchmark configuration allows setting `batch_size: 2000` in `config/benchmark.yaml` to avoid transaction memory overflow during ingestion.

### 2.2 In-Memory Exhaustion (Memgraph)
- **Limit**: Memgraph stores data in physical RAM. Ingestion of large graph datasets requires at least 2GB of free host memory.
- **Resolution**: Adjust `MEMGRAPH_MAX_MEMORY` or allocate at least 4GB of RAM to Docker daemon.

---

## 3. Dataset Preparation Issues

### 3.1 Network Timeout Downloading SNAP Archive
- **Symptom**: `requests.exceptions.ConnectionError` while contacting `snap.stanford.edu`.
- **Resolution**: Use the built-in deterministic synthetic generator fallback:
  ```bash
  python -m benchmark.cli prepare-data --synthetic-only
  ```
  This creates an identical scale-free citation graph with 34,546 nodes and 421,578 relationships matching the exact schema with fixed seed `42`.
