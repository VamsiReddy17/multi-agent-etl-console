# 🚀 Multi-Agent Pipeline & React Monitor — E2E Walkthrough

Welcome to the **Production-Ready Multi-Agent Data Engineering Pipeline**! 
This project features a real-time event-streaming pipeline (polling Kafka, transforming, validating, and loading to a PostgreSQL Data Warehouse) monitored by a premium, celestial-themed **Cosmos Development Chronicle Dashboard** on port `5173`.

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

Once booted, the high-fidelity system monitor dashboard is served on **port `5173`**:
👉 **Open your browser and navigate to**: **[http://localhost:5173](http://localhost:5173)**

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
| **Cosmos Dashboard** | `5173` | [http://localhost:5173](http://localhost:5173) |
| **WebSocket Telemetry Server** | `8085` | `ws://localhost:8085/ws` (REST: `http://localhost:8085`) |
| **Apache Airflow Web UI** | `8080` | [http://localhost:8080](http://localhost:8080) *(User: airflow / Pass: airflow)* |
| **Grafana Analytics Charts** | `3000` | [http://localhost:3000](http://localhost:3000) *(User: admin / Pass: admin)* |
| **Prometheus Telemetry Scraper** | `9090` | [http://localhost:9090](http://localhost:9090) |
| **ETL Metrics Endpoint** | `8000` | [http://localhost:8000/metrics](http://localhost:8000/metrics) |
| **PostgreSQL Data Warehouse** | `5432` | `localhost:5432` *(User: postgres / Pass: postgres_password)* |
