#!/bin/bash
# ==============================================================================
# Multi-Agent Pipeline E2E Shutdown Script
# ==============================================================================
# Set working directory to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "======================================================================"
echo "🛑 WINDING DOWN MULTI-AGENT PIPELINE ECOSYSTEM"
echo "======================================================================"

# 1. Stop local React/Vite dev server
echo "Step 1/3: Terminating local React Dashboard (Vite) dev server..."
VITE_PIDS=$(pgrep -f "vite --port 8082" || true)
if [ ! -z "$VITE_PIDS" ]; then
  kill $VITE_PIDS 2>/dev/null || true
  echo "✅ Dashboard terminated!"
else
  # Fallback to checking port 8082
  PORT_PID=$(lsof -t -i:8082 || true)
  if [ ! -z "$PORT_PID" ]; then
    kill -9 $PORT_PID 2>/dev/null || true
    echo "✅ Dashboard port 8082 cleared!"
  else
    echo "ℹ️ No active dashboard processes found."
  fi
fi

# 1b. Stop local python telemetry server on port 8085
echo "Step 1.5/3: Terminating local Telemetry Server (port 8085)..."
PORT_8085_PID=$(lsof -t -i:8085 || true)
if [ ! -z "$PORT_8085_PID" ]; then
  kill -9 $PORT_8085_PID 2>/dev/null || true
  echo "✅ Telemetry server terminated!"
else
  echo "ℹ️ No active telemetry server found."
fi

# 2. Stop loop daemons inside container
echo "Step 2/3: Terminating background ETL loop inside containers..."
docker exec prod_airflow_webserver python3 -c "import os; [os.kill(int(p), 9) for p in os.listdir('/proc') if p.isdigit() and os.path.exists(f'/proc/{p}/cmdline') and 'streaming_etl.py' in open(f'/proc/{p}/cmdline').read()]" || true
echo "✅ Container loop daemon cleared!"

# 3. Shut down Docker Compose services
echo "Step 3/3: Winding down Docker container stack..."
docker-compose down
echo "✅ Docker container services stopped!"

echo "======================================================================"
echo "🎉 ECOSYSTEM CLEANLY WINDED DOWN. SEE YOU NEXT TIME!"
echo "======================================================================"
