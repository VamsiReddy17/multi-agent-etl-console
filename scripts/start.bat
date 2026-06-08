@echo off
rem ==============================================================================
rem Windows Multi-Agent Pipeline E2E Bootstrapper Script
rem ==============================================================================
echo ======================================================================
echo 🚀 BOOTSTRAPING MULTI-AGENT DATA ENGINEERING PIPELINE (WINDOWS)
echo ======================================================================

rem 1. Spin up the complete Docker Compose Stack
echo Step 1/5: Launching Docker container services...
docker-compose up -d

rem 2. Create Kafka topics if needed
echo Step 2/5: Creating active Kafka streaming topics...
timeout /t 5 >nul
docker exec prod_kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic orders --partitions 1 --replication-factor 1
docker exec prod_kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic customers --partitions 1 --replication-factor 1
echo ✅ Topic partitions active!

rem 3. Auto-configure Airflow PostgreSQL Connection
echo Step 3/5: Auto-provisioning Airflow connections...
docker exec prod_airflow_webserver airflow connections add postgres_default --conn-type postgres --conn-host postgres --conn-schema dataware --conn-login postgres --conn-password postgres_password --conn-port 5432
echo ✅ Airflow DB connection provisioned!

rem 4. Launch Ingestion ETL Loop Daemon in background
echo Step 4/5: Launching Continuous Streaming ETL Daemon...
docker exec -d prod_airflow_webserver python3 /app/pipelines/streaming_etl.py --mode loop
echo ✅ ETL streaming loop active in background!

rem 5. Boot React + Vite Dashboard Development Server
echo Step 5/5: Booting premium Material 3 React dashboard dev server...
if exist "monitoring\dashboard" (
  cd monitoring\dashboard
  rem Launch npm dev server in a new window on port 8082
  start /B npm run dev -- --port 8082 --host
  cd ..\..
  echo ✅ React + Vite Dashboard active in background!
  echo ----------------------------------------------------------------------
  echo 🌐 Google Cloud Console UI is live at: http://localhost:8082
  echo ----------------------------------------------------------------------
) else (
  echo ⚠️ Dashboard folder missing! Skipping UI startup.
)

echo 🎉 Windows bootstrap complete! Enjoy exploring your streaming pipeline.
