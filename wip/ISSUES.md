# ⚠️ Issues Tracker

> Log every bug, error, blocker, and fix here.
> Never delete resolved issues — mark them `✅ Fixed` and explain the fix.
> This file is the IDE's memory of what went wrong and how it was solved.

---

## Issue Format

```
### ISSUE-XXX — Short Title
- **Status**: 🔴 Open | 🟡 In Progress | ✅ Fixed
- **Severity**: Critical | High | Medium | Low
- **Discovered**: YYYY-MM-DD | Session N
- **File(s)**: path/to/file.py
- **Description**: What happened
- **Error Output**: (paste exact error if available)
- **Root Cause**: Why it happened
- **Fix Applied**: What was changed
- **Fixed In**: Session N
```

---

## Open Issues

### ISSUE-011 — Missing environment variables in Airflow container services
- **Status**: ✅ Fixed
- **Severity**: Critical
- **Discovered**: 2026-05-20 | Session 2
- **File(s)**: `docker-compose.yml`
- **Description**: Running manual pipeline or Airflow tasks fails to connect to Postgres/Kafka because `POSTGRES_HOST` and `KAFKA_BROKER` default to `localhost` inside the container since the `.env` file is ignored by `.dockerignore` and not passed to compose services.
- **Error Output**:
  ```
  agents.kafka_ingestion_agent — [KafkaIngestionAgent] Connection error: NoBrokersAvailable
  ```
- **Root Cause**: The `.env` file is excluded from the Docker build context (correctly), and the compose services (`airflow_webserver`, `airflow_scheduler`, `airflow_worker`) do not load `.env` at runtime. Hence, python scripts running inside the containers default to `localhost:9092` and `localhost:5432`.
- **Fix Applied**: Added `POSTGRES_HOST: postgres` and `KAFKA_BROKER: kafka:9092` explicitly to the environment configurations of `airflow_webserver`, `airflow_scheduler`, and `airflow_worker` in `docker-compose.yml`.
- **Fixed In**: Session 2

### ISSUE-010 — Missing celery and redis in root requirements.txt
- **Status**: ✅ Fixed
- **Severity**: Critical
- **Discovered**: 2026-05-20 | Session 2
- **File(s)**: `requirements.txt`
- **Description**: Airflow scheduler and worker fail to start with `ModuleNotFoundError: No module named 'celery'`.
- **Error Output**:
  ```
  ModuleNotFoundError: No module named 'celery'
  ```
- **Root Cause**: `CeleryExecutor` is used by Airflow, which requires `celery`, `redis`, and `apache-airflow-providers-celery`. These packages were specified in `airflow/requirements.txt` but not in the root `requirements.txt` which the Dockerfile uses to build the image for all Airflow services.
- **Fix Applied**: Added `apache-airflow-providers-celery==3.1.0`, `celery==5.2.6`, and `redis==4.5.1` to the root `requirements.txt` and rebuilt the containers.
- **Fixed In**: Session 2

### ISSUE-009 — connexion v3 incompatibility with Apache Airflow 2.5.3
- **Status**: ✅ Fixed
- **Severity**: Critical
- **Discovered**: 2026-05-20 | Session 2
- **File(s)**: `requirements.txt`, `airflow/requirements.txt`
- **Description**: Airflow webserver fails to start with `TypeError: __init__() got an unexpected keyword argument 'skip_error_handlers'`.
- **Error Output**:
  ```
  File "/usr/local/lib/python3.9/site-packages/airflow/www/extensions/init_views.py", line 216, in init_api_connexion
    connexion_app = App(__name__, specification_dir=spec_dir, skip_error_handlers=True, options=options)
  TypeError: __init__() got an unexpected keyword argument 'skip_error_handlers'
  ```
- **Root Cause**: Modern `connexion` v3.3.0 was installed by pip, which has deprecated/removed the `skip_error_handlers` keyword argument. Airflow 2.5.3 requires `connexion<3.0` (specifically legacy `connexion[swagger]`).
- **Fix Applied**: Locked `connexion[swagger]==2.14.2` in both `requirements.txt` and `airflow/requirements.txt` and rebuilt the containers.
- **Fixed In**: Session 2

### ISSUE-005 — apache-airflow-providers-apache-kafka version mismatch
- **Status**: ✅ Fixed
- **Severity**: Critical
- **Discovered**: 2026-05-20 | Session 2
- **File(s)**: `requirements.txt`, `airflow/requirements.txt`
- **Description**: Pip install fails during docker-compose build because `apache-airflow-providers-apache-kafka==0.2.0` does not exist or is not installable on PyPI for Python 3.9.
- **Error Output**:
  ```
  ERROR: Could not find a version that satisfies the requirement apache-airflow-providers-apache-kafka==0.2.0
  ERROR: No matching distribution found for apache-airflow-providers-apache-kafka==0.2.0
  ```
- **Root Cause**: An invalid/non-existent package version (0.2.0) was specified in the requirements files.
- **Fix Applied**: Change the version of `apache-airflow-providers-apache-kafka` to `1.0.0` which is the first stable version of the provider package.
- **Fixed In**: Session 2

### ISSUE-006 — SQLAlchemy version conflict with Apache Airflow
- **Status**: ✅ Fixed
- **Severity**: Critical
- **Discovered**: 2026-05-20 | Session 2
- **File(s)**: `requirements.txt`, `airflow/requirements.txt`
- **Description**: Pip install fails because SQLAlchemy is locked to `2.0.0` which is incompatible with Apache Airflow 2.5.3 (which requires `sqlalchemy<2.0` and `>=1.4`).
- **Error Output**:
  ```
  ERROR: Cannot install -r requirements.txt (line 2) and sqlalchemy==2.0.0 because these package versions have conflicting dependencies.
  The conflict is caused by:
      The user requested sqlalchemy==2.0.0
      apache-airflow 2.5.3 depends on sqlalchemy<2.0 and >=1.4
  ```
- **Root Cause**: SQLAlchemy version `2.0.0` was specified, but Airflow 2.5.3 only supports SQLAlchemy `< 2.0`.
- **Fix Applied**: Downgrade SQLAlchemy version from `2.0.0` to `1.4.40` in both requirements files.
- **Fixed In**: Session 2

### ISSUE-007 — Pendulum v3 incompatibility with Apache Airflow 2.5.3
- **Status**: ✅ Fixed
- **Severity**: Critical
- **Discovered**: 2026-05-20 | Session 2
- **File(s)**: `requirements.txt`, `airflow/requirements.txt`
- **Description**: Airflow services fail to start, throwing `TypeError: 'module' object is not callable` in `pendulum.tz.timezone("UTC")`.
- **Error Output**:
  ```
    from airflow import settings
  File "/usr/local/lib/python3.9/site-packages/airflow/settings.py", line 50, in <module>
    TIMEZONE = pendulum.tz.timezone("UTC")
  TypeError: 'module' object is not callable
  ```
- **Root Cause**: Airflow 2.5.3 is built for Pendulum v2 and is incompatible with Pendulum v3, which recently released and was resolved as a dependency of `apache-airflow` because no version upper bound was specified for `pendulum` in the pip resolve graph.
- **Fix Applied**: Lock `pendulum==2.1.2` in both requirements files.
- **Fixed In**: Session 2

### ISSUE-008 — flask-session v0.8.0 incompatibility with Apache Airflow 2.5.3
- **Status**: ✅ Fixed
- **Severity**: Critical
- **Discovered**: 2026-05-20 | Session 2
- **File(s)**: `requirements.txt`, `airflow/requirements.txt`
- **Description**: Airflow database upgrade fails, throwing `ModuleNotFoundError: No module named 'flask_session.sessions'` when flask-session v0.8.0 is installed.
- **Error Output**:
  ```
    from flask_session.sessions import SqlAlchemySessionInterface
  ModuleNotFoundError: No module named 'flask_session.sessions'
  ```
- **Root Cause**: `flask-session` v0.8.0 refactored its internal folder structure, removing the `flask_session.sessions` module, which Airflow 2.5.3 relies on.
- **Fix Applied**: Locked `flask-session==0.4.0` in both `requirements.txt` and `airflow/requirements.txt` to restore compatibility.
- **Fixed In**: Session 2

---

## Anticipated Issues (Pre-emptive)

### ISSUE-001 — Airflow DB not initialised on first run
- **Status**: 🟡 Watch
- **Severity**: High
- **Discovered**: Session 1 (anticipated)
- **File(s)**: `docker-compose.yml`
- **Description**: On first `docker-compose up`, Airflow needs `airflow db upgrade` before the webserver starts. The docker-compose command already handles this (`bash -c "airflow db upgrade && airflow webserver"`), but the `airflow` database must exist in PostgreSQL first.
- **Root Cause**: PostgreSQL's `init.sql` uses `CREATE DATABASE IF NOT EXISTS airflow` — note this syntax is not standard PostgreSQL. PostgreSQL uses a different approach.
- **Fix Applied**: If the Airflow DB fails to init, manually run:
  ```bash
  docker exec prod_postgres psql -U postgres -c "CREATE DATABASE airflow;"
  docker exec prod_airflow_webserver airflow db upgrade
  docker-compose restart airflow_webserver airflow_scheduler airflow_worker
  ```
- **Fixed In**: N/A (precautionary)

---

### ISSUE-002 — `CREATE DATABASE IF NOT EXISTS` not valid in PostgreSQL
- **Status**: ✅ Fixed
- **Severity**: Medium
- **Discovered**: Session 1 (code review)
- **File(s)**: `postgres/init.sql` line 1-2
- **Description**: `CREATE DATABASE IF NOT EXISTS airflow;` is MySQL syntax. PostgreSQL does not support this.
- **Error Output**:
  ```
  ERROR:  syntax error at or near "IF"
  LINE 1: CREATE DATABASE IF NOT EXISTS airflow;
  ```
- **Root Cause**: The init.sql was written with MySQL-style syntax.
- **Fix Applied**: Replaced with PostgreSQL-compatible `DO $$ BEGIN ... END $$;` block using `pg_database` check.
- **Fixed In**: Session 1

---

### ISSUE-003 — kafka-python consumer_timeout_ms behaviour
- **Status**: 🟡 Watch
- **Severity**: Low
- **Discovered**: Session 1 (anticipated)
- **File(s)**: `agents/kafka_ingestion_agent.py`
- **Description**: When Kafka has no messages, `consumer_timeout_ms` causes the for-loop to exit cleanly. This is the intended behaviour — the agent returns 0 rows. But if Kafka is completely unreachable, the connection error may take longer than expected to surface.
- **Fix Applied**: N/A — handled by try/except in `run()`. Airflow retries on failure.
- **Fixed In**: N/A (by design)

---

### ISSUE-004 — Airflow admin user not created automatically
- **Status**: ✅ Fixed
- **Severity**: High
- **Discovered**: Session 1 (anticipated)
- **File(s)**: `scripts/docker_setup.sh`
- **Description**: The Airflow webserver starts but the default admin user (`airflow/airflow`) may not exist unless explicitly created.
- **Error Output**: Login page works but credentials rejected.
- **Fix Applied**: Added `airflow users create` command with full instructions to `scripts/docker_setup.sh` output. Users now see the exact command to run after `docker-compose up -d`.
- **Fixed In**: Session 1

### ISSUE-012 — Quality stage test quarantined threshold failure
- **Status**: ✅ Fixed
- **Severity**: High
- **Discovered**: 2026-05-21 | Session 3
- **File(s)**: `tests/test_pipeline.py`
- **Description**: During quality agent testing, supplying 2 valid records and 1 bad record resulted in a quarantine rate of 33%, which exceeded the 20% quarantine rate threshold and aborted the pipeline execution instead of loading data.
- **Error Output**:
  ```
  Quarantine rate 33.3% exceeds threshold 20.0% — aborting load
  ```
- **Root Cause**: The mock parameters specified 1 bad record inside a tiny batch of 3, leading to an artificially high bad record rate (33.3%) exceeding the 20% safety threshold.
- **Fix Applied**: Adjusted the unit/integration test mock inputs to have 5 valid records and 1 quarantined record. This yields a quarantine rate of 16.7%, staying below the 20% threshold and allowing the test to verify a successful run.
- **Fixed In**: Session 3

### ISSUE-013 — Continuous ETL loop mode terminates early inside webserver
- **Status**: ✅ Fixed
- **Severity**: Medium
- **Discovered**: 2026-05-21 | Session 4
- **File(s)**: `pipelines/config/pipeline_config.yaml`
- **Description**: The background streaming pipeline daemon automatically terminates after 10 loops, causing the metrics endpoint to become unreachable.
- **Error Output**:
  ```
  [StreamingETL] 10 consecutive empty polls — stopping
  [StreamingETL] Pipeline stopped
  ```
- **Root Cause**: The `max_empty_polls` configuration in `pipeline_config.yaml` was set to `10`, which causes the loop to exit cleanly after 10 empty pulls from Kafka.
- **Fix Applied**: Set `max_empty_polls` to `0` (indicating infinite running) in `pipeline_config.yaml`.
- **Fixed In**: Session 4

---

## Resolved Issues

*None yet — will be moved here from Open Issues once fixed.*

---

## How the IDE Should Use This File

When starting a session:
1. Read all 🔴 Open issues first
2. If running commands that touch affected files, apply fixes before running
3. After resolving an issue, update status to ✅ Fixed, add fix details
4. After discovering a new issue, add it here immediately with full context
