# 📋 Next Steps — Prioritised Backlog

> This is the prioritised list of what to do next.
> Update after every session: tick off done items, add new ones.
> The IDE reads this to understand what to work on in the current session.

---

## 🔴 Priority 1 — Critical (Do First)

### [x] Fix ISSUE-002 — PostgreSQL `CREATE DATABASE IF NOT EXISTS` syntax
- **File**: `postgres/init.sql` line 2
- **Action**: Replace MySQL syntax with valid PostgreSQL equivalent
- **Details**: See `wip/ISSUES.md` → ISSUE-002
- **Command to verify fix**:
  ```bash
  docker exec prod_postgres psql -U postgres -c "\l" | grep airflow
  ```

### [x] Fix ISSUE-004 — Create Airflow admin user
- **File**: `docker-compose.yml` or setup script
- **Action**: Add `airflow users create` command to `scripts/docker_setup.sh`
- **Details**: See `wip/ISSUES.md` → ISSUE-004

### [x] Run pytest and fix any failures
- **Command**:
  ```bash
  cd "/Users/vamsireddy/Desktop/Agents Dev/production-pipeline"
  pip install python-dotenv pyyaml psycopg2-binary kafka-python pytest
  pytest tests/ -v
  ```
- **Expected**: All 20+ test cases pass
- **If failures**: Log in `wip/ISSUES.md`, fix in place, re-run

---

## 🟡 Priority 2 — High (Do This Session)

*All high-priority tasks completed and verified.*

---

## 🟢 Priority 3 — Medium (Next Session)

### [ ] Write `airflow/plugins/` — custom Airflow sensor
- `KafkaTopicSensor` — waits until a Kafka topic has messages before triggering DAG

### [ ] Add dead letter queue
- Route quarantined records to a `dead_letter` Kafka topic instead of just logging
- Add `dead_letter_agent.py`

### [ ] Add data quality report
- After each pipeline run, generate a summary: total, valid, quarantined, error rate
- Save to `warehouse.quality_report` table

---

## 🔵 Priority 4 — Low (Future Sessions)

### [ ] BigQuery migration
- Implement `bigquery_load_agent.py`
- Update pipeline config to support GCP targets
- See `docs/BIGQUERY_MIGRATION.md`

### [ ] Cloud Pub/Sub support
- Add `pubsub_ingestion_agent.py` as alternative to Kafka
- Environment flag to switch between Kafka and Pub/Sub

### [ ] API layer
- Add a FastAPI REST endpoint to trigger pipeline runs on-demand
- `POST /pipeline/run` → triggers `streaming_etl.run_once()`
- `GET /pipeline/status` → returns latest `pipeline_execution` row

### [ ] Load testing
- Produce 10,000 messages to Kafka
- Measure pipeline throughput (rows/second)
- Tune `KAFKA_BATCH_SIZE` for optimal performance

### [ ] Retry dead-letter records
- Cron job that reads `dead_letter` topic and re-runs through pipeline
- After N retries, move to `permanent_failures` table

---

## ✅ Completed Items (Archive)

*Items moved here once fully done and verified.*

| Item | Completed | Session |
|------|-----------|---------|
| Build all 4 agents | ✅ | Session 1 |
| Build streaming ETL pipeline | ✅ | Session 1 |
| Build 2 Airflow DAGs | ✅ | Session 1 |
| Write all unit + integration tests | ✅ | Session 1 |
| Create architecture folder + diagram | ✅ | Session 1 |
| Create all 4 docs | ✅ | Session 1 |
| Create WIP memory folder | ✅ | Session 1 |
| Fix ISSUE-002: PostgreSQL CREATE DATABASE | ✅ | Session 2 |
| Fix ISSUE-004: Create Airflow admin user | ✅ | Session 2 |
| Run pytest and fix failures | ✅ | Session 2 |
| Start Docker stack & verify services | ✅ | Session 3 |
| Create Kafka topics | ✅ | Session 3 |
| Configure Airflow Postgres Connection | ✅ | Session 3 |
| Enable Airflow DAGs | ✅ | Session 3 |
| Run E2E pipeline happy-path test | ✅ | Session 3 |
| Add Prometheus + Grafana infrastructure | ✅ | Session 3 |
| Implement custom telemetry metrics | ✅ | Session 3 |
| Verify scraping UP & preloaded dashboard | ✅ | Session 4 |
| Build continuous Kafka order events generator | ✅ | Session 5 |
| Create scripts/generate_orders.sh wrapper | ✅ | Session 5 |
| Integrate order generator Docker service | ✅ | Session 5 |
| Run end-to-end telemetry pipeline successfully | ✅ | Session 5 |
| Build premium Material 3 React Monitoring Dashboard | ✅ | Session 6 |
| Create AGENT_KNOWLEDGE.md mistake tracking system | ✅ | Session 6 |
| Build E2E automated start/stop orchestrators | ✅ | Session 6 |
| Configure Git repository & push to GitHub | ✅ | Session 7 |
| Build GitHub Actions CI workflow (`ci.yml`) | ✅ | Session 7 |
| Add CONTRIBUTING.md & SECURITY.md guidelines | ✅ | Session 7 |
| Design & Build Phase 3 "The Observatory" | ✅ | Session 9 |

---

## How the IDE Should Use This File

At the **start of a session**:
1. Read all 🔴 Priority 1 items and fix issues first
2. Then work through 🟡 Priority 2 items in order
3. If time remains, start on 🟢 Priority 3

After **completing an item**:
1. Tick it off: `[x]` → `✅`
2. Move to the Completed Items table at the bottom
3. Update `wip/COMPLETIONS.md` and `wip/SESSION_LOG.md`

After **discovering a new task**:
1. Add it to the appropriate priority level
2. If it's a bug, also log in `wip/ISSUES.md`
