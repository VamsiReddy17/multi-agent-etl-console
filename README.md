# Production-Ready Multi-Agent Data Pipeline

Complete local development environment with Docker, Apache Airflow, Kafka, and PostgreSQL. Built on the multi-agent orchestration framework.

## 🎯 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Git

### Setup (5 minutes)

```bash
cd production-pipeline

# 1. Setup environment and build
./scripts/docker_setup.sh

# 2. Start all services
docker-compose up -d

# 3. Create Kafka topics
./scripts/create_topics.sh

# 4. Verify everything is running
./scripts/health_check.sh
```

### Access Services

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| **Airflow UI** | http://localhost:8080 | airflow | airflow |
| **PostgreSQL** | localhost:5432 | postgres | postgres_password |
| **Kafka** | localhost:9092 | - | - |
| **Redis** | localhost:6379 | - | - |

## 📋 Services

### PostgreSQL (Port 5432)
Local data warehouse with pre-configured schema:
- `warehouse.customers` - Customer dimension
- `warehouse.products` - Product dimension
- `warehouse.orders` - Orders fact table
- `warehouse.order_events` - Event stream from Kafka
- `warehouse.pipeline_execution` - Pipeline logs

Connect:
```bash
psql -h localhost -U postgres -d dataware
```

### Apache Kafka (Port 9092)
Streaming data broker with pre-configured topics:
- `orders` - Order events stream
- `customers` - Customer updates stream
- `products` - Product catalog stream
- `events` - Generic events stream
- `enriched_orders` - Processed orders

List topics:
```bash
docker exec prod_kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Apache Airflow (Port 8080)
Workflow orchestration platform:
- Web UI at http://localhost:8080
- DAGs for pipeline orchestration
- Celery executor with Redis backend
- Database backend for PostgreSQL

### Redis (Port 6379)
In-memory data store for Airflow Celery backend

## 📁 Project Structure

```
production-pipeline/
├── docker-compose.yml ............ Service orchestration
├── Dockerfile ................... Python image for agents
├── requirements.txt ............. Python dependencies
├── .env.example ................. Environment template
│
├── postgres/
│   ├── init.sql ................. Database schema
│   └── schemas/ ................. Additional schemas
│
├── kafka/
│   └── scripts/ ................. Topic management
│
├── airflow/
│   ├── airflow.cfg .............. Configuration
│   ├── requirements.txt ......... Airflow dependencies
│   ├── dags/ .................... DAG definitions
│   ├── plugins/ ................. Custom plugins
│   └── logs/ .................... Execution logs
│
├── agents/ ...................... Multi-agent implementations
│   ├── kafka_ingestion_agent.py
│   ├── postgres_load_agent.py
│   └── config.py
│
├── pipelines/ ................... Pipeline implementations
│   ├── streaming_etl.py
│   └── config/
│
├── scripts/ ..................... Utility scripts
│   ├── docker_setup.sh
│   ├── create_topics.sh
│   └── health_check.sh
│
├── docs/ ........................ Documentation
│   ├── SETUP.md
│   ├── AIRFLOW_GUIDE.md
│   ├── KAFKA_GUIDE.md
│   └── BIGQUERY_MIGRATION.md
│
└── tests/ ....................... Integration tests
```

## 🚀 Working with Services

### PostgreSQL

#### Connect to database
```bash
psql -h localhost -U postgres -d dataware
```

#### View tables
```sql
\dt warehouse.*
SELECT * FROM warehouse.customers;
SELECT * FROM warehouse.orders;
```

#### Monitor pipeline executions
```sql
SELECT * FROM warehouse.pipeline_execution ORDER BY created_at DESC;
```

### Kafka

#### Produce test message
```bash
docker exec prod_kafka kafka-console-producer \
  --broker-list localhost:9092 \
  --topic orders

# Type JSON messages:
{"order_id": 1, "customer_id": 101, "amount": 99.99}
```

#### Consume messages
```bash
docker exec prod_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --from-beginning
```

### Airflow

#### View DAGs
- Open http://localhost:8080
- Default credentials: airflow / airflow

#### Trigger DAG
```bash
docker exec prod_airflow_webserver airflow dags test [dag_id]
```

#### View logs
```bash
docker-compose logs -f airflow_scheduler
docker-compose logs -f airflow_worker
```

## 📊 Sample Data

The PostgreSQL schema comes with sample data:
- 5 customers
- 5 products
- 5 sample orders

Use these to test pipelines without external data sources.

## 🛠️ Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild images
docker-compose build --no-cache

# Execute command in container
docker exec prod_postgres psql -U postgres -d dataware -c "SELECT * FROM warehouse.orders"

# Health check
./scripts/health_check.sh

# Clean volumes (WARNING: deletes data)
docker-compose down -v
```

## 📈 Next Steps

1. **Run Sample Pipeline** (Phase 2)
   - Connect agents to Kafka
   - Process order events
   - Load to PostgreSQL

2. **Create Airflow DAGs** (Phase 3)
   - Orchestrate agent execution
   - Schedule regular pipelines
   - Monitor execution

3. **Add Monitoring** (Phase 4)
   - Setup dashboards
   - Add alerts
   - Track metrics

4. **Scale to BigQuery** (Phase 5)
   - Migrate schema
   - Update agents
   - Switch to cloud infrastructure

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker ps

# View service logs
docker-compose logs [service_name]

# Rebuild everything
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### PostgreSQL won't connect
```bash
# Check if container is running
docker ps | grep postgres

# Check logs
docker logs prod_postgres

# Reset database
docker-compose down -v
docker-compose up postgres -d
```

### Kafka topics not created
```bash
# Manually create topics
./scripts/create_topics.sh

# Verify topics exist
docker exec prod_kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Airflow UI not accessible
```bash
# Check webserver is running
docker ps | grep airflow_webserver

# View logs
docker logs prod_airflow_webserver

# Restart webserver
docker-compose restart airflow_webserver
```

## 📚 Documentation

- **[LOCAL_SETUP.md](docs/LOCAL_SETUP.md)** - Detailed setup guide
- **[AIRFLOW_GUIDE.md](docs/AIRFLOW_GUIDE.md)** - Airflow configuration & DAGs
- **[KAFKA_GUIDE.md](docs/KAFKA_GUIDE.md)** - Kafka topics & producers
- **[BIGQUERY_MIGRATION.md](docs/BIGQUERY_MIGRATION.md)** - Migration to production

## 🔄 Architecture

```
Kafka Topics (Streaming Data)
        ↓
[Kafka Brokers & Zookeeper]
        ↓
[Airflow DAGs - Orchestration]
        ↓
[Multi-Agent Pipeline]
  ├─ Ingestion Agents
  ├─ Transform Agents
  ├─ Quality Agents
  └─ Load Agents
        ↓
[PostgreSQL - Data Warehouse]
        ↓
[Analytics & Dashboards]
        ↓
[BigQuery - Production Scale]
```

## 📝 Environment Variables

Edit `.env` file to customize:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=dataware

# Kafka
KAFKA_BROKER=kafka:9092
KAFKA_TOPIC_ORDERS=orders

# Airflow
AIRFLOW_HOME=/app/airflow
AIRFLOW__CORE__EXECUTOR=CeleryExecutor

# Redis
REDIS_URL=redis://redis:6379/0
```

## 📈 Monitoring

Check service health:
```bash
./scripts/health_check.sh
```

View Docker stats:
```bash
docker stats
```

## 🚀 Production Deployment

For production deployment to BigQuery and cloud infrastructure, see [BIGQUERY_MIGRATION.md](docs/BIGQUERY_MIGRATION.md).

## 📞 Support

- Check logs: `docker-compose logs [service]`
- Run health check: `./scripts/health_check.sh`
- Review documentation in `docs/` folder

## 📄 License

This project is part of the Multi-Agent Data Engineering Pipelines reference architecture.

---

**Ready to start?** Run `docker-compose up -d` and visit http://localhost:8080 🚀
