#!/bin/bash

set -e

echo "🚀 Production Pipeline - Docker Setup"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Docker found"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

echo "✅ Docker Compose found"
echo ""

# Copy .env if doesn't exist
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from .env.example"
    cp .env.example .env
    echo "✅ .env created (update values if needed)"
else
    echo "⚠️  .env already exists"
fi

echo ""
echo "🐳 Building Docker images..."
docker-compose build --no-cache

echo ""
echo "✅ Docker setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start services:      docker-compose up -d"
echo "  2. Check status:        docker-compose ps"
echo "  3. Create Kafka topics: ./scripts/create_topics.sh"
echo "  4. Create Airflow user (run after docker-compose up -d):"
echo "     docker exec prod_airflow_webserver airflow users create \\"
echo "       --username airflow --password airflow \\"
echo "       --firstname Admin --lastname User \\"
echo "       --role Admin --email admin@example.com"
echo "  5. Add Postgres connection:"
echo "     docker exec prod_airflow_webserver airflow connections add postgres_default \\"
echo "       --conn-type postgres --conn-host postgres --conn-schema dataware \\"
echo "       --conn-login postgres --conn-password postgres_password --conn-port 5432"
echo "  6. Enable DAGs:"
echo "     docker exec prod_airflow_webserver airflow dags unpause streaming_etl"
echo "     docker exec prod_airflow_webserver airflow dags unpause batch_orders_etl"
echo "  7. Access Airflow UI:   http://localhost:8080  (airflow / airflow)"
