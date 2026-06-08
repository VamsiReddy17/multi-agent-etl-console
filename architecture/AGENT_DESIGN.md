# Agent Design Principles & Contracts

## Design Philosophy

Each agent in this pipeline follows the **Single Responsibility Principle** — it does exactly one job and does it well. Agents are:

- **Stateless** — no shared mutable state between runs
- **Idempotent** — safe to run multiple times with the same input
- **Independent** — testable in isolation without other agents
- **Contractual** — explicit input/output shapes defined

---

## Agent Contract (Input / Output)

Every agent follows this standard result contract:

### Input
Agents accept the **result dict** from the previous agent as their primary input.

```python
{
  "status": "success" | "error" | "skipped",
  "data": [list of record dicts],
  "rows": int,
  ...
}
```

### Output
Every agent returns a result dict:

```python
{
  "status": "success" | "error" | "skipped",
  "data": [list of record dicts],
  "rows": int,
  "duration_ms": float,
  "errors": [list of error strings],
  "error_message": str | None,
  "agent": "AgentName"
}
```

---

## Agent Specifications

### KafkaIngestionAgent

```
Input:   topics: List[str]
Output:  data: List[Dict]  ← raw decoded JSON messages

Key fields added:
  _topic      str   Kafka topic name
  _partition  int   Kafka partition
  _offset     int   Message offset
```

### TransformAgent

```
Input:   data from KafkaIngestionAgent
Output:  data: List[Dict]  ← enriched records

Fields coerced:
  order_id    → int
  customer_id → int
  product_id  → int
  quantity    → int   (default: 1)
  amount      → float
  event_type  → str   (lowercased)

Fields added:
  total_amount        float   quantity × unit_price
  processed_at        str     UTC ISO timestamp
  event_timestamp     str     UTC ISO timestamp (if missing)
  _pipeline_name      str     from config
  _pipeline_version   str     "1.0.0"
```

### QualityAgent

```
Input:   data from TransformAgent
Output:
  data:              List[Dict]  ← valid records only
  quarantined:       List[Dict]  ← failed records
  quarantined_count: int

Validation rules:
  ✓ Required: order_id, customer_id, amount
  ✓ amount > 0 and amount ≤ 1,000,000
  ✓ quantity ≥ 1
  ✓ customer_id, product_id > 0 (if present)
  ✓ No duplicate order_id within the batch
  ✓ event_type in known set (if provided)
```

### PostgresLoadAgent

```
Input:   data from QualityAgent (valid records only)
Output:
  rows_loaded: int    ← rows successfully inserted

SQL operations:
  INSERT INTO warehouse.order_events ... ON CONFLICT DO NOTHING
  INSERT INTO warehouse.pipeline_execution ... (audit log)

Idempotency: ON CONFLICT DO NOTHING prevents duplicate inserts
Atomicity:   All rows in a batch commit together or rollback together
```

---

## Agent Communication Pattern

Agents communicate by passing **result dicts** — not by shared state or direct method calls.

```python
# Pipeline orchestration (streaming_etl.py)
ingest_result   = ingestion_agent.run(topics=["orders"])
transform_result = transform_agent.run(ingest_result)
quality_result  = quality_agent.run(transform_result)
load_result     = load_agent.run(quality_result)
```

This makes each agent independently testable:

```python
# Test transform agent in isolation
fake_ingest = {"status": "success", "data": [...], "rows": 3}
result = TransformAgent().run(fake_ingest)
assert result["rows"] == 3
```

---

## Adding a New Agent

1. Create `agents/my_agent.py`
2. Implement `__init__(self, config)` and `run(self, input_result) -> dict`
3. Return a result dict with at minimum: `status`, `data`, `rows`, `agent`
4. Add to `agents/__init__.py`
5. Wire into `pipelines/streaming_etl.py`
6. Add unit tests in `tests/test_my_agent.py`

```python
class MyAgent:
    def __init__(self, config=None):
        self.config = config or default_config
        self.name = "MyAgent"

    def run(self, input_result: dict) -> dict:
        if input_result.get("status") != "success":
            return {"status": "skipped", "data": [], "rows": 0, "agent": self.name}

        records = input_result["data"]
        # ... your logic ...
        return {
            "status": "success",
            "data": processed,
            "rows": len(processed),
            "errors": [],
            "agent": self.name,
        }
```
