# 🚀 Multi-Agent Pipeline & React Monitor — E2E Walkthrough

Welcome to the **Production-Ready Multi-Agent Data Engineering Pipeline**! 
This project features a real-time event-streaming pipeline (polling Kafka, transforming, validating, and loading to a PostgreSQL Data Warehouse) monitored by a premium **Google Material 3 React System Dashboard** on port `8082`.

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
  PostgreSQL Warehouse   ← grows past 249,000+ loaded order events!
```

---

## ⚡ 1. E2E Lifecycle Automation (Quick Start)

We have built fully-automated orchestrators and desktop launcher shortcuts to handle the complete bootstrap and teardown of all container services, loop daemons, and dev servers.

### 🍏 macOS Launcher (Double-Click from Finder)

You can launch and stop the complete application stack directly from macOS Finder:

* **To Bootstrap Everything**:
  Double-click **[Start.command](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/Start.command)** in the project root folder.
  *This automatically launches Docker Desktop (if not already running), spins up all containers, verifies database health, creates streaming topics, starts the ETL daemon, and boots up the React dashboard.*

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

## 🌐 2. Exposing the Google Material 3 Dashboard

Once booted, the high-fidelity system monitor dashboard is served on **port `8082`**:
👉 **Open your browser and navigate to**: **[http://localhost:8082](http://localhost:8082)**

### Key Features:
* **Active Status Bar**: Displays active system operational state and running environment details.
* **Component Matrix**: Grid displaying Zookeeper, Kafka, Redis, Airflow, Agents, Postgres, Prometheus, and Grafana. Click any card to expand its **Side Sheet Details Panel** showing active port mappings, ping, and configuration details!
* **Live Ingestion Canvas**: Watch data packets move through the processing stages in real-time. Green nodes indicate healthy flows, while anomalies visually branch off to represent validation filters.
* **NEW - Interactive Ingestion Controllers**:
  * **Event Stream Switch**: Toggle simulated telemetry generation directly from the UI.
  * **Velocity Range Slider**: Adjust throughput dynamically from 10 events/s to 1,000 events/s.
  * **Anomaly Injector**: Scale malformed packet injection from 0% to 50% in real-time. Exceeding 20% displays a flashing red warning banner!
* **NEW - Real-Time STDOUT Stream Terminal**:
  * A monospace virtual terminal displaying live stdout logs (Kafka partition offsets, agent batch processes, isolation alerts, Postgres COPY saves) streamed directly from the background ETL container loop via WebSockets!
  * Supports terminal scroll-lock toggle and console clearing.
* **NEW - Live Postgres Warehouse Inspector**:
  * Select active target tables (`warehouse.order_events`, `warehouse.orders`, `warehouse.pipeline_execution`, and `warehouse.schema_drift_logs`!) to inspect live-updated row inserts in a structured grid fetched straight from PostgreSQL!
* **Telemetry Toggle**:
  * **Live Telemetry Mode**: Connects directly to our active WebSocket server at `ws://localhost:8085/ws` to stream real metrics, logs, and database grids!
  * **Simulation Mode**: Generates a rich, realistic local data-flow simulation if the backend is offline.
* **NEW - Quarantine Hub**:
  * A dedicated visual review panel displaying malformed events isolated in `warehouse.quarantine_events`.
  * **JSON Code Debugger Editor**: Launch a debugging workspace, edit the malformed JSON event payload, and execute transactional database reprocessing using the `POST /reprocess` backend API.
* **Agent Hub / Checklist**: View historical bug reviews and check off pre-deployment validation parameters before writing code.

---

## 🛠️ 3. Agent Learner & Mistake Board

To prevent regression bugs (such as framework package incompatibilities) during future development runs, we have established a central knowledge repository:
👉 **Review the developer checks in**: **[wip/AGENT_KNOWLEDGE.md](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/wip/AGENT_KNOWLEDGE.md)**

It records in-depth post-mortems of connexion, pendulum, flask-session, and sqlalchemy package requirements, ensuring environment stability across restarts.

---

## 📊 4. Metrics & Port Mapping Index

The local ecosystem exposes the following active interfaces once bootstrapped:

| Interface / Service | Local Port | URL |
|---------------------|------------|-----|
| **React Dashboard (Material 3)** | `8082` | [http://localhost:8082](http://localhost:8082) |
| **WebSocket Telemetry Server** | `8085` | `ws://localhost:8085/ws` (REST: `http://localhost:8085`) |
| **Apache Airflow Web UI** | `8080` | [http://localhost:8080](http://localhost:8080) *(User: airflow / Pass: airflow)* |
| **Grafana Analytics Charts** | `3000` | [http://localhost:3000](http://localhost:3000) *(User: admin / Pass: admin)* |
| **Prometheus Telemetry Scraper** | `9090` | [http://localhost:9090](http://localhost:9090) |
| **ETL Metrics Endpoint** | `8000` | [http://localhost:8000/metrics](http://localhost:8000/metrics) |
| **PostgreSQL Data Warehouse** | `5432` | `localhost:5432` *(User: postgres / Pass: postgres_password)* |
