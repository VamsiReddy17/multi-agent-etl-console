#!/bin/bash

set -e

echo "📝 Creating Kafka Topics"
echo "======================="
echo ""

KAFKA_BROKER="${KAFKA_BROKER:-kafka:9092}"
KAFKA_CONTAINER="${KAFKA_CONTAINER:-prod_kafka}"

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka broker to be ready..."
for i in {1..30}; do
    if docker exec $KAFKA_CONTAINER kafka-broker-api-versions --bootstrap-server localhost:9092 &> /dev/null; then
        echo "✅ Kafka is ready"
        break
    fi
    echo "  Attempt $i/30..."
    sleep 2
done

# Create topics
TOPICS=("orders" "customers" "products" "events" "enriched_orders" "dead_letter")

for topic in "${TOPICS[@]}"; do
    echo "Creating topic: $topic"
    docker exec $KAFKA_CONTAINER kafka-topics --create \
        --topic $topic \
        --bootstrap-server localhost:9092 \
        --partitions 1 \
        --replication-factor 1 \
        --if-not-exists
done

echo ""
echo "✅ All topics created!"
echo ""
echo "Verify with: docker exec prod_kafka kafka-topics --list --bootstrap-server localhost:9092"
