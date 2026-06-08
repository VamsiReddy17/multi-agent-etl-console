# Kafka Guide

## Topics

| Topic | Purpose | Producer |
|-------|---------|----------|
| `orders` | New order events | External systems / test producer |
| `customers` | Customer updates | CRM systems |
| `products` | Product catalog updates | Catalog service |
| `events` | Generic events | Any service |
| `enriched_orders` | Processed & enriched orders | Pipeline output |

---

## Listing Topics

```bash
docker exec prod_kafka kafka-topics \
  --list \
  --bootstrap-server localhost:9092
```

---

## Producing Test Messages

```bash
docker exec -it prod_kafka kafka-console-producer \
  --broker-list localhost:9092 \
  --topic orders
```

Paste JSON and press Enter:

```json
{"order_id": 101, "customer_id": 1, "product_id": 2, "quantity": 3, "amount": 89.97, "event_type": "order_placed"}
{"order_id": 102, "customer_id": 2, "product_id": 1, "quantity": 1, "amount": 999.99, "event_type": "order_placed"}
```

---

## Consuming Messages

```bash
# From beginning
docker exec prod_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --from-beginning

# Latest only
docker exec prod_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orders
```

---

## Checking Consumer Groups

```bash
docker exec prod_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list

docker exec prod_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group prod-pipeline-group
```

---

## Message Format

All messages must be valid JSON. Required fields for `orders` topic:

```json
{
  "order_id": 1,           // integer, required
  "customer_id": 101,      // integer, required
  "product_id": 5,         // integer, optional
  "quantity": 2,           // integer, default=1
  "amount": 49.99,         // float, required (> 0)
  "event_type": "order_placed"  // string, optional
}
```

---

## Resetting Consumer Offsets

```bash
# Reset to earliest (reprocess all messages)
docker exec prod_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group prod-pipeline-group \
  --topic orders \
  --reset-offsets \
  --to-earliest \
  --execute
```
