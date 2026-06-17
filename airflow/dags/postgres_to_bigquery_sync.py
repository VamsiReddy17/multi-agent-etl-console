"""
PostgreSQL to BigQuery ELT Sync DAG

Performs incremental replication from PostgreSQL tables to Google Cloud BigQuery.
Uses watermarking based on target table timestamps to fetch only new records.
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

def sync_postgres_to_bigquery(**context) -> None:
    """
    Query BQ watermark, extract incremental records from PG, stage to GCS, and load to BQ.
    """
    gcs_bucket = os.getenv("GCS_BUCKET_NAME", "my-etl-landing-bucket")
    gcp_conn_id = "gcp_default"
    postgres_conn_id = "postgres_default"
    
    pg_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    
    from google.cloud import bigquery
    gcp_project = os.getenv("GCP_PROJECT_ID", "dataengineering-481815")
    bq_client = bigquery.Client(project=gcp_project)
    
    dataset_id = "raw"
    table_id = "order_events"
    
    watermark = "1970-01-01 00:00:00"
    
    # 1. Fetch Watermark from BigQuery
    try:
        query = f"SELECT MAX(received_at) as max_val FROM `{bq_client.project}.{dataset_id}.{table_id}`"
        query_job = bq_client.query(query)
        results = query_job.result()
        for row in results:
            if row.max_val:
                watermark = row.max_val.strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"Retrieved BigQuery watermark: {watermark}")
    except Exception as e:
        print(f"Could not retrieve watermark from BigQuery (possibly first run). Using default: {watermark}. Error: {e}")

    # 2. Extract from PostgreSQL
    extract_query = f"""
        SELECT 
            event_id, order_id, customer_id, product_id, quantity, amount, 
            event_type, event_timestamp, received_at, processed 
        FROM 
            warehouse.order_events 
        WHERE 
            received_at > '{watermark}'
        ORDER BY 
            received_at ASC;
    """
    
    pg_conn = pg_hook.get_conn()
    cursor = pg_conn.cursor()
    cursor.execute(extract_query)
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    pg_conn.close()
    
    if not rows:
        print("No new records found since watermark. Sync skipped.")
        return
        
    print(f"Extracted {len(rows)} new records from PostgreSQL.")
    
    # 3. Format and write to JSONL
    temp_dir = tempfile.gettempdir()
    local_file_path = os.path.join(temp_dir, f"order_events_sync_{context['ds_nodash']}.json")
    
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
        table_ref = f"{bq_client.project}.{dataset_id}.{table_id}"
        
        from google.cloud import bigquery
        schema = [
            bigquery.SchemaField("event_id", "INTEGER"),
            bigquery.SchemaField("order_id", "INTEGER"),
            bigquery.SchemaField("customer_id", "INTEGER"),
            bigquery.SchemaField("product_id", "INTEGER"),
            bigquery.SchemaField("quantity", "INTEGER"),
            bigquery.SchemaField("amount", "NUMERIC"),
            bigquery.SchemaField("event_type", "STRING"),
            bigquery.SchemaField("event_timestamp", "TIMESTAMP"),
            bigquery.SchemaField("received_at", "TIMESTAMP"),
            bigquery.SchemaField("processed", "BOOLEAN"),
        ]
        with open(local_file_path, "rb") as source_file:
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                schema=schema
            )
            load_job = bq_client.load_table_from_file(source_file, table_ref, job_config=job_config)
            load_job.result()
        
        print(f"Successfully loaded data from local staged file into BigQuery table {table_ref}")
        
    except Exception as e:
        print(f"Failed to load staged file into BigQuery: {e}")
        raise e
    finally:
        if os.path.exists(local_file_path):
            os.remove(local_file_path)

with DAG(
    dag_id="postgres_to_bigquery_sync",
    description="Incremental ELT replication from PostgreSQL to BigQuery",
    default_args=DEFAULT_ARGS,
    schedule_interval="@hourly",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=["sync", "elt", "postgres", "bigquery"],
) as dag:

    trigger_sync = PythonOperator(
        task_id="sync_postgres_to_bigquery",
        python_callable=sync_postgres_to_bigquery,
    )

    trigger_sync
