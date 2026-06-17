#!/usr/bin/env python3
"""
Dead Letter Queue (DLQ) Retry Agent

Consumes records from the 'dead_letter' Kafka topic, extracts the retry count
from the headers, re-runs them through the ETL pipeline, and either:
  1. Loads them successfully to the database (if the error is resolved).
  2. Re-queues them to the DLQ (incrementing the retry count in headers) if retry_count < 3.
  3. Archives them in warehouse.permanent_failures database table if retry_count >= 3.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
import psycopg2

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.config import PipelineConfig
from agents.transform_agent import TransformAgent
from agents.quality_agent import QualityAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dlq_retry_agent")


def extract_retry_count(msg) -> int:
    """Extract retry_count from Kafka record headers."""
    retry_count = 1
    if msg.headers:
        for key, value in msg.headers:
            if key == "retry_count":
                try:
                    retry_count = int(value.decode("utf-8"))
                except ValueError:
                    pass
    return retry_count


def write_to_permanent_failures(config: PipelineConfig, record: dict, retry_count: int, error_message: str):
    """Save permanently failed record to PostgreSQL."""
    logger.info(f"[DLQ Retry] Exceeded retry limit for order {record.get('order_id')}. Saving to permanent_failures.")
    try:
        conn = psycopg2.connect(**config.db.dsn)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO warehouse.permanent_failures
                    (order_id, customer_id, product_id, quantity, amount,
                     event_type, event_timestamp, error_message, retry_count, failed_at)
                VALUES
                    (%(order_id)s, %(customer_id)s, %(product_id)s, %(quantity)s, %(amount)s,
                     %(event_type)s, %(event_timestamp)s, %(error_message)s, %(retry_count)s, NOW());
            """, {
                "order_id": record.get("order_id"),
                "customer_id": record.get("customer_id"),
                "product_id": record.get("product_id"),
                "quantity": record.get("quantity"),
                "amount": record.get("amount") or record.get("total_amount") or 0.0,
                "event_type": record.get("event_type"),
                "event_timestamp": record.get("event_timestamp"),
                "error_message": error_message,
                "retry_count": retry_count,
            })
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[DLQ Retry] Failed to write to permanent_failures: {e}")


def main():
    config = PipelineConfig()
    
    # Initialize Kafka Consumer for 'dead_letter' topic
    # Use consumer_timeout_ms=5000 to exit batch processing once topic is empty
    try:
        from kafka import KafkaConsumer, KafkaProducer
    except ImportError:
        logger.error("kafka-python is not installed. Exiting.")
        sys.exit(1)

    dlq_topic = "dead_letter"
    group_id = "dlq-retry-batch-group"
    
    logger.info(f"Connecting to Kafka broker at: {config.kafka.broker}")
    try:
        consumer = KafkaConsumer(
            dlq_topic,
            bootstrap_servers=config.kafka.broker,
            group_id=group_id,
            auto_offset_reset="earliest",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            consumer_timeout_ms=5000,  # Gracefully stop when queue is empty
        )
        producer = KafkaProducer(
            bootstrap_servers=config.kafka.broker,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    except Exception as e:
        logger.error(f"Failed to initialize Kafka connections: {e}")
        sys.exit(1)

    # Initialize Agents
    transform_agent = TransformAgent(config)
    quality_agent = QualityAgent(config)
    
    if config.load_target == "bigquery":
        from agents.bigquery_load_agent import BigQueryLoadAgent
        load_agent = BigQueryLoadAgent(config)
    else:
        from agents.postgres_load_agent import PostgresLoadAgent
        load_agent = PostgresLoadAgent(config)

    logger.info("Starting DLQ processing batch...")
    processed_count = 0
    resolved_count = 0
    requeued_count = 0
    failed_count = 0

    try:
        for msg in consumer:
            payload = msg.value
            retry_count = extract_retry_count(msg)
            processed_count += 1
            
            logger.info(f"Processing DLQ message for order {payload.get('order_id')} (Retry attempt: {retry_count})")
            
            # Wrap payload in expected ingest stage format
            ingest_result = {
                "status": "success",
                "data": [payload],
                "rows": 1,
                "duration_ms": 0,
                "errors": [],
                "agent": "KafkaIngestionAgent",
            }

            # Run transform & quality stages
            transform_result = transform_agent.run(ingest_result)
            quality_result = quality_agent.run(transform_result)

            # If quality check is successful (and no record quarantined)
            if quality_result["status"] == "success" and len(quality_result.get("quarantined", [])) == 0:
                # Load record
                load_result = load_agent.run(quality_result)
                if load_result["status"] == "success":
                    resolved_count += 1
                    logger.info(f"✅ Successfully retried and loaded order {payload.get('order_id')}")
                else:
                    # Treat load failure as retry failure, re-queue
                    logger.warning(f"Failed to load order {payload.get('order_id')}: {load_result.get('error_message')}")
                    if retry_count < 3:
                        requeued_count += 1
                        producer.send(
                            dlq_topic,
                            value=payload,
                            headers=[("retry_count", str(retry_count + 1).encode("utf-8"))],
                        )
                    else:
                        failed_count += 1
                        write_to_permanent_failures(config, payload, retry_count, f"Load failure: {load_result.get('error_message')}")
            else:
                # Validation failed, check if we can retry
                quarantined_record = quality_result["quarantined"][0] if quality_result.get("quarantined") else payload
                err_msg = quarantined_record.get("error_message") or "Failed quality checks"
                
                if retry_count < 3:
                    requeued_count += 1
                    logger.info(f"🔄 Validation failed for order {payload.get('order_id')} ({err_msg}). Re-queuing with incremented retry count.")
                    producer.send(
                        dlq_topic,
                        value=payload,
                        headers=[("retry_count", str(retry_count + 1).encode("utf-8"))],
                    )
                else:
                    failed_count += 1
                    write_to_permanent_failures(config, payload, retry_count, err_msg)

        producer.flush()
    except Exception as exc:
        logger.exception(f"Exception during DLQ retry loop: {exc}")
    finally:
        consumer.close()
        producer.close()
        load_agent.close()
        logger.info(
            f"DLQ batch finished. Processed: {processed_count} | "
            f"Resolved & Loaded: {resolved_count} | "
            f"Re-queued: {requeued_count} | "
            f"Permanent Failures: {failed_count}"
        )


if __name__ == "__main__":
    main()
