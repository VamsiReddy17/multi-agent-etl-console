# 🧠 Agent Knowledge & Mistake Prevention Base

> **ATTENTION FUTURE AGENTS:** Read this file before making any changes to dependencies, configurations, or orchestration layers. 
> This is a curated repository of past mistakes, bugs, and lessons learned in this project to prevent regressions and ensure code safety.

---

## 📋 1. Pre-Deployment Validation Checklist

Before building or launching the pipeline environment, verify:
- [x] **SQLAlchemy** is locked to `sqlalchemy==1.4.40` (do NOT allow upgrades to `>=2.0.0`).
- [x] **Pendulum** is locked to `pendulum==2.1.2` (do NOT allow upgrades to `>=3.0.0`).
- [x] **Connexion** is locked to `connexion[swagger]==2.14.2` (do NOT allow upgrades to `>=3.0.0`).
- [x] **Flask-Session** is locked to `flask-session==0.4.0` (do NOT allow upgrades to `>=0.8.0`).
- [x] **Quality Ingestion Thresholds** do not inject more than 20% anomalies in mock environments, otherwise the Quality Agent triggers a safety abort.
- [x] **Agent Config Properties** are dynamically mapped from `pipeline_config.yaml` to `self.config` before instantiating agents.
- [x] **Postgres Quarantine DLQ** is fully operational via psycopg2 transactional integration in PostgresLoadAgent.
- [x] **WebSocket Telemetry Server** runs on port 8085 with full CORS enablement.
- [x] **Referee Ingestion Controller** adjusts ingestion batch sizes dynamically based on calculated Kafka consumer lag.
- [x] **Dynamic Schema Drift Detection** automatically logs warnings to warehouse.schema_drift_logs when non-standard column structures are detected.

---

## 🛠️ 2. Bugs Post-Mortems & Agent Learnings

### BUG-001: Airflow API Connexion V3 Crash
* **Symptoms**: Airflow webserver fails to start up, throwing:
  `TypeError: __init__() got an unexpected keyword argument 'skip_error_handlers'`
* **Root Cause**: `connexion` v3.3.0+ was resolved by pip, which deprecated and removed the legacy `skip_error_handlers` keyword used by Airflow 2.5.3's API layer.
* **Fix**: Force-locked `connexion[swagger]==2.14.2` in `requirements.txt` and `airflow/requirements.txt`.
* **Agent Learning**: Always lock major framework dependencies. Never assume transitive sub-dependencies are backward-compatible.

### BUG-002: Pendulum Timezone Incompatibility
* **Symptoms**: Scheduler and webserver containers crash instantly, throwing:
  `TypeError: 'module' object is not callable` in `pendulum.tz.timezone("UTC")`
* **Root Cause**: Pendulum v3.0.0+ was recently released and changed timezone methods. Airflow 2.5.3 was designed for Pendulum v2 and crashes under v3.
* **Fix**: Force-locked `pendulum==2.1.2` in requirements files.
* **Agent Learning**: When a mature framework like Airflow fails to boot after dependency upgrades, look for recent major releases of core time/timezone dependencies.

### BUG-003: Flask-Session Namespace Shift
* **Symptoms**: Container database initialization fails with:
  `ModuleNotFoundError: No module named 'flask_session.sessions'`
* **Root Cause**: `flask-session` v0.8.0 refactored its directory structure, moving and removing internal session interfaces that Airflow 2.5.3 explicitly imports.
* **Fix**: Locked `flask-session==0.4.0` to restore internal module namespaces.
* **Agent Learning**: Lock the entire dependency ecosystem when dealing with specific, older versions of enterprise frameworks.

### BUG-004: SQLAlchemy v2.0 Breaking Upgrades
* **Symptoms**: Conflicting dependency resolver errors during Docker build:
  `apache-airflow 2.5.3 depends on sqlalchemy<2.0 and >=1.4; user requested sqlalchemy==2.0.0`
* **Root Cause**: The project was initially created with `sqlalchemy==2.0.0` in `requirements.txt`, which violates Airflow 2.5.3's strict `< 2.0` ceiling constraints.
* **Fix**: Downgraded to `sqlalchemy==1.4.40` across requirements.
* **Agent Learning**: Always check compatibility bounds of the main framework (Airflow) before locking supporting ORMs or databases.

### BUG-005: Quality Stage Mock Threshold Abort
* **Symptoms**: Unit and E2E pipeline tests failed with:
  `Quarantine rate 33.3% exceeds threshold 20.0% — aborting load`
* **Root Cause**: The mock dataset had 2 valid records and 1 bad record, yielding a 33.3% quarantine rate which exceeded the 20% safety abort limit.
* **Fix**: Expanded mock inputs to 5 valid records and 1 bad record, dropping the rate to a safe 16.7% and letting tests verify a successful load.
* **Agent Learning**: In testing systems, ensure your sample proportions correctly mirror the realistic production threshold rules.

### BUG-006: Batch-Size Config Propagation Failure
* **Symptoms**: Despite configuring `batch_size: 2000` in YAML, metrics showed exactly 100 events were processed per batch.
* **Root Cause**: `StreamingETL.__init__` was instantiating agents without passing the YAML-derived properties to the `PipelineConfig` instance, letting the agent fall back to default environment values.
* **Fix**: Explicitly mapped `batch_size` and `poll_timeout_ms` from `yaml_cfg` to `self.config` prior to agent creation.
* **Agent Learning**: Tracing and print statements are highly effective. If metrics show a constant number, verify configuration values actually propagate to your active clients.

### BUG-007: Detached Container Daemon Log Capture Defect
* **Symptoms**: Standard docker logs for the webserver did not output the `streaming_etl.py` logging statements when run in detached (`-d`) mode.
* **Root Cause**: `docker exec -d` spawns a detached background process whose stdout streams are not captured by the main container supervisor daemon logs.
* **Fix**: Redirected `streaming_etl.py` output inside `start.sh` using `bash -c "... > /app/pipelines/streaming_etl.log 2>&1"`, allowing the host server to trace it locally.
* **Agent Learning**: When launching background loop executors in docker, pipe logs to shared volumes to guarantee observability.

### BUG-008: Missing websockets Dependency on Telemetry Bootstrap
* **Symptoms**: Telemetry server failed to boot on host, throwing: `ModuleNotFoundError: No module named 'websockets'`.
* **Root Cause**: While FastAPI and Uvicorn were pre-installed on the user's host environment, the `websockets` sub-dependency was absent, preventing uvicorn ASGI protocol resolution.
* **Fix**: Programmatically installed the `websockets` library via pip3 package manager.
* **Agent Learning**: Verify availability of WebSocket protocol parsing packages alongside standard HTTP libraries before spinning up live gateways.

---

## 📡 3. Advanced Integration Process (DLQ, WebSockets, & Referee)

As we integrate live data pipelines with real database quarantines, interactive agent toggles, WebSockets, and CDC, future models must respect the following integration steps and bug preventions:

### 📋 Integration Process Guidelines

1. **Database Schema Initialization**:
   * **Rule**: Always define database quarantine and logs tables in the PostgreSQL init files (`sql/` directory) first.
   * **Reason**: Prevents downstream python psycopg2 insertions from crashing with `RelationDoesNotExist` errors if agents boot before tables are provisioned.
2. **WebSocket Port Coordination**:
   * **Rule**: Run the WebSocket server on a dedicated, non-Airflow port (e.g. `8085`) and handle socket reuse.
   * **Reason**: Avoids address collision errors if multiple agents or dev servers attempt to bind to the same listener during restarts.
3. **psycopg2 Quarantine Transaction Safety**:
   * **Rule**: When executing a human-in-the-loop reprocessing operation, the payload edit and database migration must be executed in a single atomic transaction block.
   * **Reason**: Prevents concurrency issues and guarantees the quarantined row is cleanly removed from the quarantine store if and only if it is successfully loaded into the order fact table.

### ⚠️ Bugs & Risks Preventative Board

* **BUG-007 (Potential): WebSocket Port Binder Address Already in Use**
  * *Prevention*: In the FastAPI / Python web server, always configure standard socket options to allow address reuse:
    ```python
    import socket
    socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ```
* **BUG-008 (Potential): Quarantine Double-Insertion on Fact Conflict**
  * *Prevention*: Ensure that your target database reprocessor uses `ON CONFLICT (order_id) DO UPDATE` or `DO NOTHING` to prevent primary key constraint failures if a row was partially loaded before quarantine.
* **BUG-009 (Potential): Dynamic Schema Drift Column Limit Exhaustion**
  * *Prevention*: Always limit the maximum size of dynamically logged schema drift field columns to prevent SQL injection or buffer overflows when analyzing custom user keys.
