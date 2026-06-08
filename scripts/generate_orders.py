#!/usr/bin/env python3
"""
Continuous Kafka Order Generator

Publishes realistic fake order events to the Kafka 'orders' topic.
Intentionally injects ~10% bad records to test the Quality Agent's quarantine logic.
"""

import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("order_generator")

# Product Catalog
PRODUCTS = {
    1: {"name": "Laptop", "price": 999.99},
    2: {"name": "Mouse", "price": 29.99},
    3: {"name": "Keyboard", "price": 79.99},
    4: {"name": "Monitor", "price": 299.99},
    5: {"name": "Desk Chair", "price": 199.99},
}

EVENT_TYPES = ["order_placed", "order_updated", "order_cancelled"]


def get_producer(broker: str) -> KafkaProducer:
    """Initialize and return a KafkaProducer connection."""
    logger.info(f"Connecting to Kafka broker at: {broker}")
    retries = 5
    delay = 2
    for i in range(retries):
        try:
            return KafkaProducer(
                bootstrap_servers=broker,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                request_timeout_ms=5000,
            )
        except KafkaError as e:
            if i == retries - 1:
                raise e
            logger.warning(f"Connection failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2


def generate_valid_order(order_id: int) -> dict:
    """Generate a realistic, completely valid order event."""
    customer_id = random.randint(1, 5)
    product_id = random.randint(1, 5)
    quantity = random.randint(1, 10)
    
    # Calculate amount realistically
    price = PRODUCTS[product_id]["price"]
    amount = round(price * quantity, 2)
    
    # event_type is mostly order_placed (80%), sometimes updated (15%) or cancelled (5%)
    event_roll = random.random()
    if event_roll < 0.80:
        event_type = "order_placed"
    elif event_roll < 0.95:
        event_type = "order_updated"
    else:
        event_type = "order_cancelled"
        
    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "product_id": product_id,
        "quantity": quantity,
        "amount": amount,
        "event_type": event_type,
    }


def inject_anomaly(order: dict, sent_orders_history: list) -> (dict, str):
    """
    Intentionally corrupts or alters a valid order to create a 'bad' record,
    returning the modified dict and a description of the injected anomaly.
    """
    corrupted_order = order.copy()
    anomaly_type = random.choice([
        "missing_order_id",
        "missing_customer_id",
        "missing_amount",
        "negative_amount",
        "zero_quantity",
        "zero_amount",
        "string_amount",
        "invalid_event_type",
        "duplicate_order_id"
    ])
    
    if anomaly_type == "missing_order_id":
        corrupted_order.pop("order_id", None)
        desc = "Missing order_id"
    elif anomaly_type == "missing_customer_id":
        corrupted_order.pop("customer_id", None)
        desc = "Missing customer_id"
    elif anomaly_type == "missing_amount":
        corrupted_order.pop("amount", None)
        desc = "Missing amount"
    elif anomaly_type == "negative_amount":
        corrupted_order["amount"] = -round(random.uniform(5.0, 100.0), 2)
        desc = f"Negative amount ({corrupted_order['amount']})"
    elif anomaly_type == "zero_quantity":
        corrupted_order["quantity"] = 0
        desc = "Zero quantity"
    elif anomaly_type == "zero_amount":
        corrupted_order["amount"] = 0.0
        desc = "Zero amount"
    elif anomaly_type == "string_amount":
        corrupted_order["amount"] = "forty-two"
        desc = "String value for amount ('forty-two')"
    elif anomaly_type == "invalid_event_type":
        corrupted_order["event_type"] = "order_returned"
        desc = "Invalid event_type ('order_returned')"
    elif anomaly_type == "duplicate_order_id" and sent_orders_history:
        # Reuse a previously sent valid order ID
        dup_id = random.choice(sent_orders_history)
        corrupted_order["order_id"] = dup_id
        desc = f"Duplicate order ID ({dup_id})"
    else:
        # Fallback to invalid event type if no history
        corrupted_order["event_type"] = "unknown_action"
        desc = "Invalid event_type ('unknown_action')"
        
    return corrupted_order, desc


def main():
    parser = argparse.ArgumentParser(description="Continuous Kafka Order Generator")
    parser.add_argument(
        "--rate",
        type=float,
        default=1.0,
        help="Messages per second (default: 1.0)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Total messages to send (default: 0 = infinite)",
    )
    parser.add_argument(
        "--bad-rate",
        type=float,
        default=0.1,
        help="Fraction of bad records to generate (default: 0.1)",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="orders",
        help="Kafka topic to publish events to (default: 'orders')",
    )
    parser.add_argument(
        "--broker",
        type=str,
        default=None,
        help="Kafka broker address (default: KAFKA_BROKER env var or 'localhost:9092')",
    )
    args = parser.parse_args()

    broker = args.broker or os.getenv("KAFKA_BROKER", "localhost:9092")
    
    try:
        producer = get_producer(broker)
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        sys.exit(1)

    logger.info(
        f"Starting data generation | Rate: {args.rate} msg/sec | "
        f"Target: {args.topic} | Bad Rate: {args.bad_rate:.1%}"
    )

    # State variables
    # Start auto-incrementing order ID at 1000 to keep it separate from sample data (1-5)
    current_order_id = 1000
    sent_orders_history = []
    max_history_len = 100
    
    sent_count = 0
    interval = 1.0 / args.rate if args.rate > 0 else 1.0

    try:
        while True:
            # Generate base valid order
            order = generate_valid_order(current_order_id)
            current_order_id += 1
            
            # Check if this should be a bad record
            is_bad = random.random() < args.bad_rate
            
            if is_bad:
                message, anomaly_desc = inject_anomaly(order, sent_orders_history)
                log_prefix = f"⚠️ [ANOMALY - {anomaly_desc}]"
            else:
                message = order
                log_prefix = "✅ [VALID]"
                # Save order ID to history for future duplicates
                sent_orders_history.append(message["order_id"])
                if len(sent_orders_history) > max_history_len:
                    sent_orders_history.pop(0)
            
            # Publish to Kafka
            try:
                future = producer.send(args.topic, message)
                # Wait for acknowledgment
                record_metadata = future.get(timeout=5)
                
                logger.info(
                    f"{log_prefix} Order {message.get('order_id', 'N/A')} sent to "
                    f"partition {record_metadata.partition} at offset {record_metadata.offset}"
                )
            except Exception as publish_error:
                logger.error(f"Failed to publish message: {publish_error}")
            
            sent_count += 1
            if args.count > 0 and sent_count >= args.count:
                logger.info(f"Finished sending target of {args.count} messages.")
                break
                
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("Loop interrupted by user.")
    finally:
        logger.info("Closing producer connection.")
        producer.close()
        logger.info("Producer stopped.")


if __name__ == "__main__":
    main()
