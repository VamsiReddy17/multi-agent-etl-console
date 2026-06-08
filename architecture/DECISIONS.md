# Architecture Decision Records (ADRs)

Architecture Decision Records capture **why** key design choices were made.

---

## ADR-001 — Use Apache Kafka as the Message Broker

**Status**: Accepted
**Date**: 2024-01-01

### Context
The pipeline needs to ingest real-time event streams from external systems. We need durability, replay capability, and decoupling between producers and consumers.

### Decision
Use **Apache Kafka** as the central message broker.

### Reasons
- Industry standard for high-throughput streaming
- Message durability — events are persisted on disk
- Consumer groups allow multiple pipelines to read independently
- Replay capability — reset offsets to reprocess historical data
- Decouples producers from the pipeline completely

### Consequences
- Requires Zookeeper (or KRaft) to manage broker state
- Additional operational complexity vs. simple REST ingestion
- Enables future fan-out to multiple consumers

---

## ADR-002 — Multi-Agent Sequential Pattern

**Status**: Accepted
**Date**: 2024-01-01

### Context
The pipeline needs Ingest, Transform, Quality, and Load stages. We need clear separation of concerns and independent testability.

### Decision
Use a **sequential multi-agent pattern** where each stage is an independent class (agent) that accepts a result dict and returns a result dict.

### Reasons
- Single Responsibility Principle — each agent does one job
- Agents are independently unit-testable without mocking the whole chain
- Easy to add/remove stages without affecting others
- Result dicts create a clear interface contract
- Matches the reference architecture in `multi-agent-pipelines/`

### Consequences
- Slight overhead from dict serialisation between stages
- Sequential (not parallel) — acceptable for batch sizes ≤ 10,000 rows

---

## ADR-003 — Apache Airflow for Orchestration

**Status**: Accepted
**Date**: 2024-01-01

### Context
The pipeline needs scheduling, retry logic, monitoring, and a management UI.

### Decision
Use **Apache Airflow** with Celery executor backed by Redis.

### Reasons
- Rich DAG-based orchestration with visual UI
- Built-in retry with exponential backoff
- Task-level failure isolation (one task fails, others complete)
- XCom for passing data between tasks
- Celery allows distributed worker scaling
- Large ecosystem of providers (Postgres, Kafka, GCP, etc.)

### Alternatives Considered
- **Cron**: Simple but no monitoring, retry, or UI
- **Prefect**: Good but adds external dependency
- **Dagster**: More modern but steeper learning curve

---

## ADR-004 — PostgreSQL as Local Data Warehouse

**Status**: Accepted (transitional)
**Date**: 2024-01-01

### Context
Need a structured data warehouse for development. Production will use BigQuery.

### Decision
Use **PostgreSQL** locally with the `warehouse` schema mirroring the BigQuery target schema.

### Reasons
- Zero-cost local development
- Schema can be kept identical to BigQuery (column types map cleanly)
- psycopg2 is mature and well-tested
- Docker image is lightweight (alpine)
- Easier than setting up BigQuery credentials locally

### Migration Path
See `docs/BIGQUERY_MIGRATION.md` for the migration guide to BigQuery.

---

## ADR-005 — Result Dict Pattern (not Exceptions) for Agent Errors

**Status**: Accepted
**Date**: 2024-01-01

### Context
When an agent encounters a bad record or upstream failure, we need to decide: raise an exception or return an error result?

### Decision
Agents return **result dicts with `status="error"` or `status="skipped"`** instead of raising exceptions for expected failure modes. Exceptions are only raised for truly unexpected errors.

### Reasons
- Downstream agents can inspect status and skip gracefully
- Partial success is expressible (97 valid + 3 quarantined)
- Easier to test error paths without try/except in tests
- Airflow tasks raise exceptions only when the whole task should retry

### Consequences
- Callers must check `result["status"]` — cannot rely on exceptions alone
- Unexpected exceptions (e.g., import errors) still propagate normally

---

## ADR-006 — Quarantine Pattern for Invalid Records

**Status**: Accepted
**Date**: 2024-01-01

### Context
Some records will inevitably fail quality checks. We can either reject the whole batch or filter bad records and continue.

### Decision
Invalid records are **quarantined** (separated, logged) and the remaining valid records are loaded. A configurable threshold aborts the load if too many records are quarantined.

### Reasons
- One bad record shouldn't block 99 valid ones
- Quarantine threshold (`quality.quarantine_threshold=0.2`) catches systemic issues
- Logged errors allow investigation without data loss
- Idempotent loads mean replaying after a fix is safe

### Threshold Configuration
```yaml
# pipelines/config/pipeline_config.yaml
quality:
  quarantine_threshold: 0.2   # Abort if >20% quarantined
```
