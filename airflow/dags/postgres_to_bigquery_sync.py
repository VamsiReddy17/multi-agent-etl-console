"""
PostgreSQL to BigQuery Multi-Table ELT Sync DAG

Performs incremental and full-overwrite replication from PostgreSQL schema tables
to Google Cloud BigQuery 'nebula_raw_zone' dataset.
"""

from datetime import datetime, timedelta
import json
import os
import tempfile
from decimal import Decimal

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

# Table configuration mapping
TABLE_CONFIGS = {
    "customers": {
        "postgres_table": "warehouse.customers",
        "bq_table": "customers",
        "sync_mode": "full_overwrite",
        "watermark_column": None,
        "schema": [
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "name", "type": "STRING"},
            {"name": "email", "type": "STRING"},
            {"name": "country", "type": "STRING"},
            {"name": "created_at", "type": "TIMESTAMP"},
            {"name": "updated_at", "type": "TIMESTAMP"},
        ]
    },
    "products": {
        "postgres_table": "warehouse.products",
        "bq_table": "products",
        "sync_mode": "full_overwrite",
        "watermark_column": None,
        "schema": [
            {"name": "product_id", "type": "INTEGER"},
            {"name": "name", "type": "STRING"},
            {"name": "category", "type": "STRING"},
            {"name": "price", "type": "NUMERIC"},
            {"name": "created_at", "type": "TIMESTAMP"},
        ]
    },
    "orders": {
        "postgres_table": "warehouse.orders",
        "bq_table": "orders",
        "sync_mode": "incremental",
        "watermark_column": "created_at",
        "schema": [
            {"name": "order_id", "type": "INTEGER"},
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "product_id", "type": "INTEGER"},
            {"name": "order_date", "type": "TIMESTAMP"},
            {"name": "quantity", "type": "INTEGER"},
            {"name": "unit_price", "type": "NUMERIC"},
            {"name": "total_amount", "type": "NUMERIC"},
            {"name": "status", "type": "STRING"},
            {"name": "created_at", "type": "TIMESTAMP"},
            {"name": "processed_at", "type": "TIMESTAMP"},
        ]
    },
    "order_events": {
        "postgres_table": "warehouse.order_events",
        "bq_table": "order_events",
        "sync_mode": "incremental",
        "watermark_column": "received_at",
        "schema": [
            {"name": "event_id", "type": "INTEGER"},
            {"name": "order_id", "type": "INTEGER"},
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "product_id", "type": "INTEGER"},
            {"name": "quantity", "type": "INTEGER"},
            {"name": "amount", "type": "NUMERIC"},
            {"name": "event_type", "type": "STRING"},
            {"name": "event_timestamp", "type": "TIMESTAMP"},
            {"name": "received_at", "type": "TIMESTAMP"},
            {"name": "processed", "type": "BOOLEAN"},
        ]
    },
    "quarantine_events": {
        "postgres_table": "warehouse.quarantine_events",
        "bq_table": "quarantine_events",
        "sync_mode": "incremental",
        "watermark_column": "quarantined_at",
        "schema": [
            {"name": "quarantine_id", "type": "INTEGER"},
            {"name": "order_id", "type": "INTEGER"},
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "product_id", "type": "INTEGER"},
            {"name": "quantity", "type": "INTEGER"},
            {"name": "amount", "type": "NUMERIC"},
            {"name": "event_type", "type": "STRING"},
            {"name": "event_timestamp", "type": "TIMESTAMP"},
            {"name": "error_message", "type": "STRING"},
            {"name": "quarantined_at", "type": "TIMESTAMP"},
            {"name": "resolved", "type": "BOOLEAN"},
        ]
    },
    "permanent_failures": {
        "postgres_table": "warehouse.permanent_failures",
        "bq_table": "permanent_failures",
        "sync_mode": "incremental",
        "watermark_column": "failed_at",
        "schema": [
            {"name": "failure_id", "type": "INTEGER"},
            {"name": "order_id", "type": "INTEGER"},
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "product_id", "type": "INTEGER"},
            {"name": "quantity", "type": "INTEGER"},
            {"name": "amount", "type": "NUMERIC"},
            {"name": "event_type", "type": "STRING"},
            {"name": "event_timestamp", "type": "TIMESTAMP"},
            {"name": "error_message", "type": "STRING"},
            {"name": "failed_at", "type": "TIMESTAMP"},
            {"name": "retry_count", "type": "INTEGER"},
        ]
    },
    "quality_report": {
        "postgres_table": "warehouse.quality_report",
        "bq_table": "quality_report",
        "sync_mode": "incremental",
        "watermark_column": "created_at",
        "schema": [
            {"name": "report_id", "type": "INTEGER"},
            {"name": "pipeline_name", "type": "STRING"},
            {"name": "start_time", "type": "TIMESTAMP"},
            {"name": "end_time", "type": "TIMESTAMP"},
            {"name": "total_records", "type": "INTEGER"},
            {"name": "valid_records", "type": "INTEGER"},
            {"name": "quarantined_records", "type": "INTEGER"},
            {"name": "error_rate", "type": "NUMERIC"},
            {"name": "created_at", "type": "TIMESTAMP"},
        ]
    },
    "pipeline_execution": {
        "postgres_table": "warehouse.pipeline_execution",
        "bq_table": "pipeline_execution",
        "sync_mode": "incremental",
        "watermark_column": "created_at",
        "schema": [
            {"name": "execution_id", "type": "INTEGER"},
            {"name": "pipeline_name", "type": "STRING"},
            {"name": "start_time", "type": "TIMESTAMP"},
            {"name": "end_time", "type": "TIMESTAMP"},
            {"name": "status", "type": "STRING"},
            {"name": "rows_processed", "type": "INTEGER"},
            {"name": "error_message", "type": "STRING"},
            {"name": "created_at", "type": "TIMESTAMP"},
        ]
    }
}


def sync_postgres_to_bigquery(table_name: str, **context) -> None:
    """
    Sync a single PostgreSQL table to BigQuery.
    Handles incremental watermark replication or full overwrite sync based on configurations.
    """
    postgres_conn_id = "postgres_default"
    pg_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    
    from google.cloud import bigquery
    gcp_project = os.getenv("GCP_PROJECT_ID", "dataengineering-481815")
    bq_client = bigquery.Client(project=gcp_project)
    
    config = TABLE_CONFIGS[table_name]
    pg_table = config["postgres_table"]
    bq_table = config["bq_table"]
    sync_mode = config["sync_mode"]
    watermark_column = config["watermark_column"]
    
    dataset_id = "nebula_raw_zone"
    table_ref = f"{bq_client.project}.{dataset_id}.{bq_table}"
    
    # Define BigQuery schema fields
    schema = []
    for field in config["schema"]:
        schema.append(bigquery.SchemaField(field["name"], field["type"]))
        
    # Ensure BigQuery table exists
    try:
        bq_client.get_table(table_ref)
    except Exception:
        print(f"Table '{bq_table}' not found in BQ. Creating it...")
        table = bigquery.Table(table_ref, schema=schema)
        bq_client.create_table(table)
        
    write_disposition = bigquery.WriteDisposition.WRITE_APPEND
    extract_query = f"SELECT * FROM {pg_table}"
    
    # 1. Handle Incremental Watermark Replications
    if sync_mode == "incremental":
        watermark = "1970-01-01 00:00:00"
        try:
            watermark_query = f"SELECT MAX({watermark_column}) as max_val FROM `{table_ref}`"
            query_job = bq_client.query(watermark_query)
            results = query_job.result()
            for row in results:
                if row.max_val:
                    watermark = row.max_val.strftime("%Y-%m-%d %H:%M:%S.%f")
            print(f"Retrieved BigQuery watermark for {bq_table}: {watermark}")
        except Exception as e:
            print(f"Could not retrieve watermark for {bq_table} (possibly first run). Using default: {watermark}. Error: {e}")
            
        extract_query = f"""
            SELECT * 
            FROM {pg_table} 
            WHERE {watermark_column} > '{watermark}'
            ORDER BY {watermark_column} ASC;
        """
    else:
        # Full Overwrite Sync Mode
        print(f"Syncing table '{bq_table}' in FULL OVERWRITE mode.")
        write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        
    # 2. Extract from PostgreSQL
    pg_conn = pg_hook.get_conn()
    cursor = pg_conn.cursor()
    cursor.execute(extract_query)
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    pg_conn.close()
    
    if not rows:
        print(f"No new records found for {bq_table} since watermark. Sync skipped.")
        return
        
    print(f"Extracted {len(rows)} records from PostgreSQL table {pg_table}.")
    
    # 3. Format and write to JSONL
    temp_dir = tempfile.gettempdir()
    local_file_path = os.path.join(temp_dir, f"{bq_table}_sync_{context['ds_nodash']}.json")
    
    with open(local_file_path, "w") as f:
        for row in rows:
            record = dict(zip(columns, row))
            for k, v in record.items():
                if isinstance(v, datetime):
                    record[k] = v.isoformat()
                elif isinstance(v, Decimal):
                    record[k] = float(v)
            f.write(json.dumps(record) + "\n")
            
    print(f"Staged {len(rows)} records locally at {local_file_path}")
    
    # 4. Load directly into BigQuery from local JSONL
    try:
        with open(local_file_path, "rb") as source_file:
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=write_disposition,
                schema=schema
            )
            load_job = bq_client.load_table_from_file(source_file, table_ref, job_config=job_config)
            load_job.result()
        
        print(f"Successfully loaded data from local staged file into BigQuery table {table_ref}")
    except Exception as e:
        print(f"Failed to load staged file into BigQuery table {table_ref}: {e}")
        raise e
    finally:
        if os.path.exists(local_file_path):
            os.remove(local_file_path)


with DAG(
    dag_id="postgres_to_bigquery_sync",
    description="Multi-table incremental and full-overwrite ELT replication from PostgreSQL to BigQuery",
    default_args=DEFAULT_ARGS,
    schedule_interval="@hourly",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=["sync", "elt", "postgres", "bigquery"],
) as dag:

    for table_id in TABLE_CONFIGS.keys():
        trigger_sync = PythonOperator(
            task_id=f"sync_{table_id}",
            python_callable=sync_postgres_to_bigquery,
            op_kwargs={"table_name": table_id},
        )
