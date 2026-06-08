# Production Pipeline — Architecture

This folder contains the complete architecture documentation and diagrams for the production multi-agent data pipeline.

## Contents

| File | Description |
|------|-------------|
| `architecture_diagram.png` | Full system architecture diagram |
| `ARCHITECTURE.md` | Detailed written architecture guide |
| `DATA_FLOW.md` | Step-by-step data flow walkthrough |
| `AGENT_DESIGN.md` | Agent design principles and contracts |
| `DECISIONS.md` | Architecture Decision Records (ADRs) |

---

## Quick Visual Overview

![Architecture Diagram](./architecture_diagram.png)

---

## One-Line Summary

> External events → **Kafka** → **4-Agent Pipeline** (Ingest → Transform → Quality → Load) → **PostgreSQL**, orchestrated by **Apache Airflow** every 5 minutes.
