# 📊 Load Testing & Performance Benchmarks

This report logs the performance and throughput measurements of the Multi-Agent ETL pipeline when processing a batch of **10000** order events.

- **Broker**: `kafka:9092`
- **Test Topic**: `load_test_orders`
- **Anomaly Ratio**: `10.0%`
- **Date**: `2026-06-17 07:15:30 UTC`

---

## 📈 Performance Summary Table

| Batch Size | Processed Rows | Total Time (s) | Consumer Throughput (rows/sec) | Avg Batch Latency (ms) | Total Batches |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **100** | 10000 | 5.15s | **1941.85** | 50.3ms | 100 |
| **500** | 10000 | 4.86s | **2056.39** | 242.7ms | 20 |
| **1000** | 10000 | 4.74s | **2110.73** | 473.0ms | 10 |
| **2000** | 10000 | 4.74s | **2110.80** | 946.2ms | 5 |
| **5000** | 10000 | 4.7s | **2125.65** | 2349.5ms | 2 |

---

## 🏆 Tuning Recommendation

Based on the measurements, the **optimal** batch configuration for this environment is:
- **Optimal Batch Size**: `5000`
- **Peak Ingestion Rate**: `2125.65 rows/second`
- **Average Batch Latency**: `2349.5 ms`

> [!TIP]
> Higher batch sizes decrease the network round-trip overhead of Kafka polling and Postgres atomic database commits, yielding maximum throughput. However, very large batches (e.g. 5,000+) can increase memory footprint and slightly increase single-batch latency.

