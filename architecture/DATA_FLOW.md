# Data Flow — Step by Step

This document traces the exact journey of a single order event from producer to database.

![Architecture Diagram](./architecture_diagram.png)

---

## Scenario: An order is placed on an e-commerce platform

### Step 1 — Event Published to Kafka

An external system publishes a raw JSON message to the `orders` topic:

```json
{
  "order_id": "201",
  "customer_id": "3",
  "product_id": "2",
  "quantity": "2",
  "amount": "49.99",
  "event_type": "ORDER_PLACED"
}
```

> Note: fields are strings at this stage — no type guarantees from the producer.

---

### Step 2 — Airflow Triggers the Pipeline (every 5 min)

The `streaming_etl` DAG fires its first task: **ingest**.

---

### Step 3 — Kafka Ingestion Agent polls the topic

```
KafkaIngestionAgent.run(topics=["orders"])
```

- Connects to `localhost:9092`
- Polls up to `batch_size=100` messages
- Decodes each message from bytes → JSON
- Adds metadata: `_topic`, `_partition`, `_offset`
- Returns:

```python
{
  "status": "success",
  "rows": 1,
  "data": [{
    "order_id": "201",
    "customer_id": "3",
    "product_id": "2",
    "quantity": "2",
    "amount": "49.99",
    "event_type": "ORDER_PLACED",
    "_topic": "orders",
    "_offset": 57
  }]
}
```

---

### Step 4 — Transform Agent enriches the record

```
TransformAgent.run(ingest_result)
```

Transformations applied:
- `"201"` → `201` (int)
- `"3"` → `3` (int)
- `"49.99"` → `49.99` (float)
- `"2"` → `2` (int)
- `total_amount` = `2 × 49.99` = `99.98`
- `event_type` = `"ORDER_PLACED"` → `"order_placed"` (lowercase)
- `processed_at` = `"2024-01-15T08:30:00+00:00"` (UTC timestamp added)
- `_pipeline_name` = `"streaming-etl"`
- `_pipeline_version` = `"1.0.0"`

Returns enriched record with all fields properly typed.

---

### Step 5 — Quality Agent validates the record

```
QualityAgent.run(transform_result)
```

Checks performed:

| Check | Value | Result |
|-------|-------|--------|
| `order_id` present | `201` | ✅ Pass |
| `customer_id` present | `3` | ✅ Pass |
| `amount` present | `49.99` | ✅ Pass |
| `amount > 0` | `49.99 > 0` | ✅ Pass |
| `amount ≤ 1,000,000` | Yes | ✅ Pass |
| `quantity ≥ 1` | `2 ≥ 1` | ✅ Pass |
| `customer_id > 0` | `3 > 0` | ✅ Pass |
| Duplicate `order_id` in batch | Not a duplicate | ✅ Pass |
| `event_type` known | `"order_placed"` ∈ known set | ✅ Pass |

Record moves to **valid** set. Result:

```python
{
  "status": "success",
  "rows": 1,          # valid records
  "quarantined_count": 0
}
```

---

### Step 6 — PostgreSQL Load Agent inserts the record

```
PostgresLoadAgent.run(quality_result)
```

Executes:

```sql
INSERT INTO warehouse.order_events
  (order_id, customer_id, product_id, quantity, amount,
   event_type, event_timestamp, received_at, processed)
VALUES
  (201, 3, 2, 2, 49.99,
   'order_placed', '2024-01-15T08:30:00', NOW(), FALSE)
ON CONFLICT DO NOTHING;
```

Then logs the run:

```sql
INSERT INTO warehouse.pipeline_execution
  (pipeline_name, start_time, end_time, status, rows_processed)
VALUES
  ('streaming-etl', '2024-01-15T08:30:00', '2024-01-15T08:30:01', 'success', 1);
```

---

### Step 7 — Data is in the warehouse ✅

```sql
SELECT * FROM warehouse.order_events WHERE order_id = 201;

-- Returns:
event_id | order_id | customer_id | product_id | quantity | amount | event_type   | processed
---------+----------+-------------+------------+----------+--------+--------------+-----------
      42 |      201 |           3 |          2 |        2 |  49.99 | order_placed | f
```

---

## What Happens to a Bad Record

If a record arrives with `amount = 0`:

```json
{"order_id": 999, "customer_id": 1, "amount": 0}
```

1. **Ingestion** — accepted (no content filtering at this stage)
2. **Transform** — enriched, `total_amount = 0`
3. **Quality** — ❌ FAILS `amount > 0` check → moved to **quarantined** set
4. **Load** — quarantined records are **never inserted**
5. The failure is logged with the error reason

---

## Batch Flow Summary

```
Kafka Poll (100 msgs)
       │
       ▼
Transform (100 → 100 enriched)
       │
       ▼
Quality Check
   │         │
   ▼         ▼
Valid (97)   Quarantined (3)
   │                │
   ▼                ▼
PostgreSQL    Logged + skipped
  Insert
(97 rows)
       │
       ▼
pipeline_execution log entry
```
