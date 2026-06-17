#!/usr/bin/env python3
"""
High-Throughput Load Testing Script

Benchmarks the multi-agent ETL pipeline using various Kafka batch sizes.
Produces exactly 10,000 messages to a designated topic, then processes them
while measuring ingestion rates, database writing latency, and overall throughput.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipelines.streaming_etl import StreamingETL
from agents.config import PipelineConfig
from scripts.generate_orders import generate_valid_order, inject_anomaly

# Setup logger for load test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("load_test")


def create_test_topic(broker: str, topic: str):
    """Ensure that the target benchmarking topic exists in Kafka."""
    logger.info(f"Connecting to Kafka AdminClient at: {broker}")
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=broker, client_id="load_test_admin")
        topic_list = [NewTopic(name=topic, num_partitions=1, replication_factor=1)]
        try:
            admin_client.create_topics(new_topics=topic_list, validate_only=False)
            logger.info(f"Created Kafka topic: {topic}")
        except TopicAlreadyExistsError:
            logger.info(f"Kafka topic '{topic}' already exists.")
        finally:
            admin_client.close()
    except Exception as e:
        logger.error(f"Failed to check/create topic '{topic}': {e}")
        raise e


def produce_benchmark_data(broker: str, topic: str, count: int, bad_rate: float) -> float:
    """Publishes JSON order events to Kafka as fast as possible."""
    logger.info(f"Initializing high-throughput Kafka producer to push {count} messages...")
    
    producer = KafkaProducer(
        bootstrap_servers=broker,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks=1,
        linger_ms=5,
        batch_size=131072,  # 128KB buffer
        buffer_memory=33554432,  # 32MB
    )
    
    start_time = time.time()
    sent_orders_history = []
    
    for i in range(count):
        order_id = 20000 + i
        order = generate_valid_order(order_id)
        
        is_bad = (i % int(1.0 / bad_rate)) == 0 if bad_rate > 0 else False
        if is_bad:
            message, _ = inject_anomaly(order, sent_orders_history)
        else:
            message = order
            sent_orders_history.append(message["order_id"])
            if len(sent_orders_history) > 100:
                sent_orders_history.pop(0)
                
        producer.send(topic, message)
        
        if (i + 1) % 2000 == 0:
            logger.info(f"Buffered {i + 1} / {count} messages...")
            
    logger.info("Flushing producer buffers...")
    producer.flush()
    duration = time.time() - start_time
    producer.close()
    
    rate = count / duration
    logger.info(f"Published {count} messages in {duration:.2f} seconds ({rate:.2f} msg/sec).")
    return duration


def run_consume_benchmark(broker: str, topic: str, batch_size: int, total_messages: int) -> dict:
    """Runs the ETL pipeline to consume messages with the specified batch size."""
    logger.info(f"Starting consumer benchmark for batch_size: {batch_size}")
    
    # Configure a unique consumer group to start from the beginning of the topic
    timestamp = int(time.time())
    group_id = f"load-test-group-{batch_size}-{timestamp}"
    
    config = PipelineConfig()
    config.kafka.broker = broker
    config.kafka.group_id = group_id
    config.kafka.topics = [topic]
    config.kafka.auto_offset_reset = "earliest"
    
    pipeline = StreamingETL(config=config)
    
    # Force the target batch size in the configuration overrides
    if "kafka" not in pipeline.yaml_cfg:
        pipeline.yaml_cfg["kafka"] = {}
    pipeline.yaml_cfg["kafka"]["batch_size"] = batch_size
    
    # Set log level to WARNING to keep the output console clean
    if "pipeline" not in pipeline.yaml_cfg:
        pipeline.yaml_cfg["pipeline"] = {}
    pipeline.yaml_cfg["pipeline"]["log_level"] = "WARNING"
    
    # Mock get_kafka_lag to return 0 to prevent the Referee dynamic controller from overwriting batch_size
    pipeline.get_kafka_lag = lambda: 0
    
    start_time = time.time()
    total_processed = 0
    batch_count = 0
    total_latencies = 0.0
    
    try:
        while total_processed < total_messages:
            summary = pipeline.run_once(topics=[topic])
            status = summary["status"]
            
            # Find the rows processed by the ingest agent
            ingest_stage = next((s for s in summary["stages"] if s.get("agent") == "KafkaIngestionAgent"), None)
            rows_polled = ingest_stage.get("rows", 0) if ingest_stage else 0
            
            if rows_polled == 0 or status == "no_data":
                logger.info(f"No more data received. Ingested total: {total_processed}")
                break
                
            total_processed += rows_polled
            batch_count += 1
            total_latencies += summary["total_ms"]
            
    finally:
        pipeline._cleanup()
        
    duration = time.time() - start_time
    throughput = total_processed / duration if duration > 0 else 0
    avg_batch_latency = total_latencies / batch_count if batch_count > 0 else 0
    
    logger.info(f"Completed: processed {total_processed} rows in {duration:.2f}s ({throughput:.2f} rows/sec)")
    
    return {
        "batch_size": batch_size,
        "processed": total_processed,
        "duration_sec": round(duration, 2),
        "throughput": round(throughput, 2),
        "avg_batch_latency_ms": round(avg_batch_latency, 2),
        "batches": batch_count,
    }


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Pipeline Load Testing Framework")
    parser.add_argument("--broker", type=str, default=None, help="Kafka broker address")
    parser.add_argument("--topic", type=str, default="load_test_orders", help="Kafka topic for load tests")
    parser.add_argument("--count", type=int, default=10000, help="Total messages to produce")
    parser.add_argument("--bad-rate", type=float, default=0.1, help="Simulated bad record fraction")
    args = parser.parse_args()
    
    broker = args.broker or os.getenv("KAFKA_BROKER", "localhost:9092")
    
    create_test_topic(broker, args.topic)
    
    # 1. Generate & publish load test data
    produce_benchmark_data(broker, args.topic, args.count, args.bad_rate)
    
    # 2. Parametric Consumer Benchmark Runs
    batch_sizes = [100, 500, 1000, 2000, 5000]
    results = []
    
    for bs in batch_sizes:
        res = run_consume_benchmark(broker, args.topic, bs, args.count)
        results.append(res)
        
    # Print nice ASCII Table
    print("\n" + "=" * 80)
    print("                      LOAD TEST THROUGHPUT BENCHMARK RESULTS")
    print("=" * 80)
    print(f"| {'Batch Size':<12} | {'Processed':<12} | {'Time (s)':<12} | {'Throughput (r/s)':<16} | {'Avg Batch (ms)':<14} |")
    print("-" * 80)
    for r in results:
        print(f"| {r['batch_size']:<12} | {r['processed']:<12} | {r['duration_sec']:<12} | {r['throughput']:<16} | {r['avg_batch_latency_ms']:<14} |")
    print("=" * 80)
    
    # Write to wip/LOAD_TEST_RESULTS.md
    # Determine dynamic path relative to this script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_path = os.path.join(project_root, "wip", "LOAD_TEST_RESULTS.md")
    logger.info(f"Saving benchmark report to {output_path}...")
    
    # Identify the optimal batch size
    optimal = max(results, key=lambda x: x["throughput"])
    
    markdown_content = f"""# 📊 Load Testing & Performance Benchmarks

This report logs the performance and throughput measurements of the Multi-Agent ETL pipeline when processing a batch of **{args.count}** order events.

- **Broker**: `{broker}`
- **Test Topic**: `{args.topic}`
- **Anomaly Ratio**: `{args.bad_rate:.1%}`
- **Date**: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`

---

## 📈 Performance Summary Table

| Batch Size | Processed Rows | Total Time (s) | Consumer Throughput (rows/sec) | Avg Batch Latency (ms) | Total Batches |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in results:
        markdown_content += f"| **{r['batch_size']}** | {r['processed']} | {r['duration_sec']}s | **{r['throughput']:.2f}** | {r['avg_batch_latency_ms']:.1f}ms | {r['batches']} |\n"
        
    markdown_content += f"""
---

## 🏆 Tuning Recommendation

Based on the measurements, the **optimal** batch configuration for this environment is:
- **Optimal Batch Size**: `{optimal['batch_size']}`
- **Peak Ingestion Rate**: `{optimal['throughput']:.2f} rows/second`
- **Average Batch Latency**: `{optimal['avg_batch_latency_ms']:.1f} ms`

> [!TIP]
> Higher batch sizes decrease the network round-trip overhead of Kafka polling and Postgres atomic database commits, yielding maximum throughput. However, very large batches (e.g. 5,000+) can increase memory footprint and slightly increase single-batch latency.

"""
    with open(output_path, "w") as f:
        f.write(markdown_content)
    logger.info("Report exported successfully.")


if __name__ == "__main__":
    main()
