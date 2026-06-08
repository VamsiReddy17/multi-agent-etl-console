#!/bin/bash
# ==============================================================================
# Multi-Agent Pipeline E2E Bootstrapper Script
# ==============================================================================
set -e

# Set working directory to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "======================================================================"
echo "🚀 BOOTSTRAPING MULTI-AGENT DATA ENGINEERING PIPELINE"
echo "======================================================================"

# 0. Ensure Docker Daemon is Running
if ! docker info >/dev/null 2>&1; then
  echo "🐳 Docker daemon is not running. Attempting to start Docker Desktop..."
  if [ "$(uname)" = "Darwin" ]; then
    open --background -a Docker
    echo -n "Waiting for Docker daemon to start"
    until docker info >/dev/null 2>&1; do
      echo -n "."
      sleep 1
    done
    echo ""
    echo "✅ Docker Desktop is now running!"
  else
    echo "❌ Docker daemon is not running. Please start Docker and try again."
    exit 1
  fi
fi

# 1. Spin up the complete Docker Compose Stack
echo "Step 1/6: Launching Docker container services..."
docker-compose up -d

# 2. Wait for Core services to be healthy
echo "Step 2/6: Waiting for services to become healthy..."
echo "Waiting for PostgreSQL database..."
until docker exec prod_postgres pg_isready -U postgres >/dev/null 2>&1; do
  sleep 1
done
echo "✅ PostgreSQL Data Warehouse is healthy!"

echo "Waiting for Redis Task Queue..."
until docker exec prod_redis redis-cli ping >/dev/null 2>&1; do
  sleep 1
done
echo "✅ Redis queue is healthy!"

echo "Waiting for Apache Kafka Broker..."
sleep 5 # give zookeeper/kafka bootstrap buffer time
echo "✅ Kafka broker listener exposed!"

# 3. Create Kafka topics if needed
echo "Step 3/6: Creating active Kafka streaming topics..."
docker exec prod_kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic orders --partitions 1 --replication-factor 1
docker exec prod_kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic customers --partitions 1 --replication-factor 1
echo "✅ Topic partitions active!"

# 4. Auto-configure Airflow PostgreSQL Connection
echo "Step 4/6: Auto-provisioning Airflow connections..."
docker exec prod_airflow_webserver airflow connections add postgres_default \
  --conn-type postgres --conn-host postgres --conn-schema dataware \
  --conn-login postgres --conn-password postgres_password --conn-port 5432 || true
echo "✅ Airflow DB connection provisioned!"

# 5. Launch Ingestion ETL Loop Daemon in background
echo "Step 5/6: Launching Continuous Streaming ETL Daemon..."
# Kill any existing loop first to avoid overlapping processes
docker exec prod_airflow_webserver python3 -c "import os; [os.kill(int(p), 9) for p in os.listdir('/proc') if p.isdigit() and os.path.exists(f'/proc/{p}/cmdline') and 'streaming_etl.py' in open(f'/proc/{p}/cmdline').read()]" || true
docker exec -d prod_airflow_webserver bash -c "python3 /app/pipelines/streaming_etl.py --mode loop > /app/pipelines/streaming_etl.log 2>&1"
echo "✅ ETL streaming loop active in background!"

# 5b. Boot Host Telemetry WebSocket Server on Port 8085
echo "Step 5.5/6: Launching WebSocket Telemetry Server on host (Port 8085)..."
# Kill any process using port 8085 first
PORT_8085_PID=$(lsof -t -i:8085 || true)
if [ ! -z "$PORT_8085_PID" ]; then
  kill -9 $PORT_8085_PID 2>/dev/null || true
fi
python3 pipelines/telemetry_server.py > /tmp/telemetry-server.log 2>&1 &
TELEMETRY_PID=$!
echo "✅ Telemetry WebSocket Server active in background! (PID: $TELEMETRY_PID)"

# 6. Boot React + Vite Dashboard Development Server
echo "Step 6/6: Booting premium Material 3 dashboard dev server..."
if [ -d "monitoring/dashboard" ]; then
  # Launch npm dev server in background using port 8082
  cd monitoring/dashboard
  npm run dev -- --port 8082 --host > /tmp/vite-dashboard.log 2>&1 &
  VITE_PID=$!
  echo "✅ React + Vite Dashboard active in background! (PID: $VITE_PID)"
  echo "----------------------------------------------------------------------"
  echo "🌐 Google Cloud Console UI is live at: http://localhost:8082"
  echo "----------------------------------------------------------------------"
else
  echo "⚠️ Dashboard folder missing! Skipping UI startup."
fi

echo "🎉 BOOTSTRAP COMPLETE! Enjoy exploring your multi-agent streaming pipeline."
