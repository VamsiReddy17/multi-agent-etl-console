@echo off
rem ==============================================================================
rem Windows Multi-Agent Pipeline E2E Shutdown Script
rem ==============================================================================
echo ======================================================================
echo 🛑 WINDING DOWN MULTI-AGENT PIPELINE ECOSYSTEM (WINDOWS)
echo ======================================================================

rem 1. Stop loop daemons inside container
echo Step 1/3: Terminating background ETL loop inside containers...
docker exec prod_airflow_webserver python3 -c "import os; [os.kill(int(p), 9) for p in os.listdir('/proc') if p.isdigit() and os.path.exists(f'/proc/{p}/cmdline') and 'streaming_etl.py' in open(f'/proc/{p}/cmdline').read()]" >nul 2>&1
echo ✅ Container loop daemon cleared!

rem 2. Shut down Docker Compose services
echo Step 2/3: Winding down Docker container stack...
docker-compose down
echo ✅ Docker container services stopped!

rem 3. Stop local dev servers
echo Step 3/3: Cleaning up port 8082 allocations...
taskkill /IM node.exe /F >nul 2>&1
echo ✅ Clean up complete!

echo ======================================================================
echo 🎉 ECOSYSTEM CLEANLY WINDED DOWN.
echo ======================================================================
