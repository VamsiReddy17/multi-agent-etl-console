# 🚀 Multi-Agent Pipeline & React Monitor — E2E Walkthrough

Welcome to the **Production-Ready Multi-Agent Data Engineering Pipeline**! 
This project features a real-time event-streaming pipeline (polling Kafka, transforming, validating, and loading to a PostgreSQL Data Warehouse) monitored by a premium, celestial-themed **Cosmos Development Chronicle Dashboard** on port `8082`.

---

## 🏗️ Core System Topology

```
   Kafka Topic "orders"  ← continuous event generation (250 msg/s)
           ↓
   Kafka Ingestion Agent ← polls batches of 2,000 messages
           ↓
      Transform Agent    ← type coercions, calculates order totals
           ↓
       Quality Agent     ← validates schemas, quarantines bad records (~10%)
           ↓
    PostgreSQL Loader    ← high-performance bulk database insertions
           ↓
  PostgreSQL Warehouse   ← grows past 109,000+ loaded order events!
```

---

## ⚡ 1. E2E Lifecycle Automation (Quick Start)

We have built fully-automated orchestrators and desktop launcher shortcuts to handle the complete bootstrap and teardown of all container services, loop daemons, and dev servers.

### 🍏 macOS Launcher (Double-Click from Finder)

You can launch and stop the complete application stack directly from macOS Finder:

* **To Bootstrap Everything**:
  Double-click **[Start.command](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/Start.command)** in the project root folder.
  *This automatically launches Docker Desktop (if not already running), spins up all containers, verifies database health, creates streaming topics, starts the ETL daemon, and boots up the React dashboard.*

- **Historical Backfill Sync**: Created [backfill_bigquery.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/scripts/backfill_bigquery.py) under `scripts/` to execute safe, chunk-by-chunk migration of PostgreSQL history to BigQuery via GCS staging using Application Default Credentials (ADC).

---

## Bypassing GCS & Direct BigQuery Loading (Session 17)

We resolved the Google Cloud client library dependencies, overcame billing account constraints on the GCP projects, and verified the entire PostgreSQL to BigQuery ELT pipeline:

### 1. Direct BigQuery Loading Implementation (Bypassing GCS)
- **Problem**: The GCP projects (`dataengineering-481815` and `pipeline-pulse1`) did not have active billing accounts, throwing `403 Forbidden` errors during GCS bucket creation.
- **Solution**: Re-engineered the backfill script ([backfill_bigquery.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/scripts/backfill_bigquery.py)) and the incremental sync DAG ([postgres_to_bigquery_sync.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/airflow/dags/postgres_to_bigquery_sync.py)) to upload data directly using BigQuery's `load_table_from_file` client API. This bypassed GCS staging entirely, allowing the ELT pipeline to run under the free **BigQuery Sandbox** tier.
- **Schema Mapping**: Explicitly defined the table schema in `LoadJobConfig` in the sync DAG to prevent type mismatch errors (autodetecting `amount` as `FLOAT` instead of `NUMERIC`).

### 2. Docker & Airflow Environment Updates
- **GCP credentials**: Updated [docker-compose.yml](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/docker-compose.yml) to mount the host's Application Default Credentials (`~/.config/gcloud:/root/.config/gcloud:ro`) and link `.env` variables to containerized Airflow and API services.
- **Plugin import pathing**: Fixed a plugin loading crash in [kafka_topic_sensor.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/airflow/plugins/kafka_topic_sensor.py) by appending `/app` to `sys.path`.
- **Worker PID recovery**: Recovered the Airflow worker container by removing the stale pidfile `airflow-worker.pid`.

### 3. Looker Dashboard View Optimization
- **File**: [reporting_views.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/bigquery/transformations/reporting_views.sql)
- **Change**: Removed the `WHERE processed = true` clause from the view `warehouse.orders_reporting`. This enables Looker Studio to display all successfully loaded events without waiting for PostgreSQL's daily processing cycle.

### 4. Verification & Testing
- **Backfill**: Executed `backfill_bigquery.py`, successfully loading all **2,063,482** historical order events into BigQuery.
- **DAG Execution**: Triggered `postgres_to_bigquery_sync` in Airflow; all tasks succeeded, updating the BigQuery raw table to **2,208,177** rows.
- **Tests**: Executed the test suite in the API container; **all 58 tests passed successfully** with zero Airflow DAG errors.

* **To Stop & Clean Up**:
  Double-click **[Stop.command](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/Stop.command)** in the project root folder.
  *This cleanly shuts down active ETL streams, terminates the local dashboard server, and winds down the Docker container stack.*

### 🖥️ Command-Line alternative (macOS/Linux Terminal)

If you prefer to run them from your terminal:

* **To Bootstrap Everything**:
  ```bash
  ./scripts/start.sh
  ```

* **To Stop & Clean Up**:
  ```bash
  ./scripts/stop.sh
  ```

### 🪟 Windows (Batch CMD)

* **To Bootstrap Everything**:
  ```cmd
  scripts\start.bat
  ```

* **To Stop & Clean Up**:
  ```cmd
  scripts\stop.bat
  ```

---

## 🌐 2. Exposing the Cosmos Dashboard

Once booted, the high-fidelity system monitor dashboard is served on **port `8082`**:
👉 **Open your browser and navigate to**: **[http://localhost:8082](http://localhost:8082)**

### Key Features by Tab:

1. **The Nebula (Session History Timeline)**:
   * View all development sessions (Sessions 1–9) rendered as nebula stages on an animated vertical timeline.
   * Expand each card to see the goals, activities, bugs found, and resolution details.
   * Includes a real-time Search Bar to filter sessions by title or description text.

2. **The Asteroid Belt (Errors & Bug Tracker)**:
   * Displays all pipeline issues as detailed space-debris cards (Critical, High, Medium, Low).
   * Displays root cause analysis, fix narratives, code snippets, and lessons learned.
   * Features a search input and chip-based severity filter.

3. **The Pulsar Log (Development Narrative Log)**:
   * Reads like a periodic signal log book. Contains pull quotes, major milestones, and error logs per session.

4. **The Solar Core (Live Pipeline Metrics & Telemetry)**:
   * Shows real-time counters (loaded records, throughput, quarantine rate, successful runs).
   * **Sparkline Mini-Charts**: Displays 20-point trailing history graphs for instant trend detection.
   * Includes controls to toggle simulation/live modes, speed, and anomaly rates.
   * Virtual scrolling stdout log terminal and database inspector.

5. **The Constellation (Live Data Flow Canvas)**:
   * Particle canvas showing live database data flowing through agent orbs. Red particles show quarantined anomalies, green/blue represent clean records.

6. **The Orion Array (System Topology & Health)**:
   * Health panel showing status of all 13 services. Clicking cards expands system specs.
   * Interactive switches to stop/start services and simulate cascading network failures.

7. **The Event Horizon (Anomaly Isolation Hub)**:
   * View and modify quarantined records using a dark code editor, and re-inject them into the pipeline.

---

## ⚡ 3. The Observatory Power-User Features

* **⌘K / Ctrl+K Command Palette**:
  * Trigger `Cmd+K` (macOS) or `Ctrl+K` (Windows/Linux) to open the palette search window. Jump to any tab, toggle simulation states, or find specific session chapters, bugs, and services.
* **🔢 Keyboard Shortcuts**:
  * Navigate tabs instantly by pressing number keys `1-7` (deactivated while typing in inputs).
  * Close the palette with `Esc`.
* **♿ Accessibility & Reduced Motion**:
  * Full support for `prefers-reduced-motion` media queries which immediately freezes canvas particle loops and stops all transitions.
* **🖨️ Print Styles**:
  * Clean black-and-white print styles built to format logs, code bases, and metrics for reports.

---

## 🛠️ 4. Agent Learner & Mistake Board

To prevent regression bugs (such as framework package incompatibilities) during future development runs, we have established a central knowledge repository:
👉 **Review the developer checks in**: **[wip/AGENT_KNOWLEDGE.md](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/wip/AGENT_KNOWLEDGE.md)**

---

## 📊 5. Metrics & Port Mapping Index

The local ecosystem exposes the following active interfaces once bootstrapped:

| Interface / Service | Local Port | URL |
|---------------------|------------|-----|
| **Cosmos Dashboard** | `8082` | [http://localhost:8082](http://localhost:8082) |
| **WebSocket Telemetry Server** | `8085` | `ws://localhost:8085/ws` (REST: `http://localhost:8085`) |
| **Apache Airflow Web UI** | `8080` | [http://localhost:8080](http://localhost:8080) *(User: airflow / Pass: airflow)* |
| **Grafana Analytics Charts** | `3000` | [http://localhost:3000](http://localhost:3000) *(User: admin / Pass: admin)* |
| **Prometheus Telemetry Scraper** | `9090` | [http://localhost:9090](http://localhost:9090) |
| **ETL Metrics Endpoint** | `8000` | [http://localhost:8000/metrics](http://localhost:8000/metrics) |
| **FastAPI REST API Layer** | `8081` | [http://localhost:8081](http://localhost:8081) |
| **PostgreSQL Data Warehouse** | `5432` | `localhost:5432` *(User: postgres / Pass: postgres_password)* |
