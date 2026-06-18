# Local Setup Guide

This guide details how to bootstrap, configure, run, and verify the Multi-Agent ETL Pipeline and Cosmos Chronicle Dashboard locally on your host PC.

---

## 🏗️ High-Level System Architecture & Component Mapping

Our development environment is comprised of local streaming components orchestrated together and bridged securely to the cloud:

```
                  ┌────────────────────────────────────────────────────────────┐
                  │                 Local PC (Docker Host)                     │
                  │                                                            │
                  │  ┌──────────────┐      ┌─────────────┐      ┌───────────┐  │
                  │  │  PostgreSQL  │ ◄─── │ Postgres    │ ◄─── │           │  │
                  │  │   (:5432)    │      │ Load Agent  │      │           │  │
                  │  └──────────────┘      └─────────────┘      │           │  │
                  │                                             │           │  │
                  │  ┌──────────────┐      ┌─────────────┐      │  Quality  │  │
┌─────────────┐   │  │ Apache Kafka │ ───► │ Ingestion   │ ───► │  Agent    │  │
│ Order Gen   │ ─►│   (:9092)    │      │ Agent       │      │           │  │
└─────────────┘   │  └──────┬───────┘      └─────────────┘      │           │  │
                  │         │                                   │           │  │
                  │         ▼ (lag check)                       │           │  │
                  │  ┌──────────────┐      ┌─────────────┐      │           │  │
                  │  │  Airflow     │      │ BigQuery    │ ◄─── └─────┬─────┘  │
                  │  │  Scheduler   │      │ Load Agent  │            │ (Clean)
                  │  └──────────────┘      └──────┬──────┘            │
                  │                               │                   ▼ (Quarantined)
                  │  ┌──────────────┐             │             ┌───────────┐
                  │  │  FastAPI API │             │             │Dead Letter│
                  │  │   (:8081)    │             │             │Agent (DLQ)│
                  │  └──────────────┘             │             └─────┬─────┘
                  │                               │                   │
                  └───────────────────────────────┼───────────────────┼────────┘
                                                  │ (HTTPS)           │ (Kafka Topic)
                                                  ▼                   ▼
                                    ┌───────────────────────────┬───────────┐
                                    │      Google Cloud GCP     │ Local Kafka
                                    │                           │ (dead_letter)
                                    │ ┌───────────────────────┐ │
                                    │ │   BigQuery Dataset    │ │
                                    │ │  (nebula_raw_zone)    │ │
                                    │ └───────────────────────┘ │
                                    └───────────────────────────┘
```

### What Individual Components Do:
* **Kafka Generator**: Continuously generates random mock transactions and streams them as JSON into the `orders` topic.
* **Apache Kafka (`:9092`)**: Acts as our event broker, queueing incoming transaction payloads durably.
* **Ingestion Agent**: Pulls raw messages from Kafka, decodes them, and processes batch inputs.
* **Transform Agent**: Handles typings, normalizations, and calculates total order metrics.
* **Quality Agent**: Validates inputs against strict rule profiles, isolating corrupt data.
* **Dead Letter Agent (DLQ)**: Publishes quarantined payloads to the `dead_letter` Kafka topic.
* **Postgres Load Agent**: Inserts validated records in batches into local PostgreSQL tables.
* **BigQuery Load Agent**: Streams clean JSONL payloads directly to BigQuery tables using the Python Client.
* **FastAPI Orchestrator (`:8081`)**: Provides REST endpoints (`/pipeline/run`, `/pipeline/status`) to trigger runs and check metrics dynamically.
* **Airflow Web UI (`:8080`)**: Manages pipelines, triggers DAGs, and monitors task logs.
* **Cosmos UI Dashboard (`:5173`)**: Offers an interactive celestial-themed chronicle web page displaying metrics, topologies, timeline histories, and editors.

---

## 🛠️ Step-by-Step Installation & Setup

### 1. Prerequisites
Ensure you have the following installed on your host system:
* **Docker Desktop** (with Docker Compose)
* **Python 3.9+** (with `pip` and virtual environment support)
* **Google Cloud SDK** (required for BigQuery replication)

### 2. Google Cloud Authentication
To authorize your local PC to synchronize data with BigQuery:
```bash
gcloud auth application-default login
```
This generates standard credentials files on your machine that are mounted directly into our Docker containers to execute secure HTTPS requests to BigQuery.

### 3. Initialize Dev Stack
1. **Configuration**:
   ```bash
   cp .env.example .env
   ```
2. **Launch Stack**:
   ```bash
   chmod +x scripts/*.sh
   ./scripts/start.sh
   ```
   This command starts PostgreSQL, Zookeeper, Kafka, Redis, Airflow, and FastAPI, provisions topics, and builds/starts the React Dashboard automatically!

### 4. Running Verification Checks
* **Run health checks**: `./scripts/health_check.sh`
* **Run tests**: `pytest tests/ -v`

### 5. Teardown
To shut down all containers and clean up resources:
```bash
./scripts/stop.sh
```
