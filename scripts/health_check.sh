#!/bin/bash

echo "🏥 Health Check - Production Pipeline Services"
echo "=============================================="
echo ""

# Check PostgreSQL
echo "📍 PostgreSQL..."
if docker exec prod_postgres pg_isready -U postgres &> /dev/null; then
    echo "  ✅ Running"
else
    echo "  ❌ Not responding"
fi

# Check Kafka
echo "📍 Kafka..."
if docker exec prod_kafka kafka-broker-api-versions --bootstrap-server localhost:9092 &> /dev/null; then
    echo "  ✅ Running"
else
    echo "  ❌ Not responding"
fi

# Check Airflow Webserver
echo "📍 Airflow Webserver..."
if curl -s http://localhost:8080/api/v1/health &> /dev/null; then
    echo "  ✅ Running"
else
    echo "  ❌ Not responding"
fi

# Check Redis
echo "📍 Redis..."
if docker exec prod_redis redis-cli ping &> /dev/null; then
    echo "  ✅ Running"
else
    echo "  ❌ Not responding"
fi

echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "💡 Tips:"
echo "  - View logs: docker-compose logs -f [service_name]"
echo "  - Connect to PostgreSQL: psql -h localhost -U postgres -d dataware"
echo "  - Access Airflow: http://localhost:8080"
echo "  - Monitor Kafka: docker exec prod_kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic [topic]"
