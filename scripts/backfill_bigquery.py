#!/usr/bin/env python3
"""
PostgreSQL to BigQuery Multi-Table Historical Backfill Script

Loads existing database tables from PostgreSQL, stages them locally in JSONL format,
and imports them into BigQuery tables in the 'nebula_raw_zone' dataset.
Uses Google Application Default Credentials (ADC) for authentication.
"""

import os
import sys
import json
import tempfile
from decimal import Decimal
from datetime import datetime

# Import PostgreSQL client
try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 is not installed. Run 'pip install psycopg2-binary'")
    sys.exit(1)

# Import Google Cloud client libraries
try:
    from google.cloud import storage
    from google.cloud import bigquery
except ImportError:
    print("Error: Google Cloud client libraries are missing. Run 'pip install google-cloud-storage google-cloud-bigquery'")
    sys.exit(1)


def load_env_vars():
    """Load config from env or fallback defaults."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ.setdefault(key, val.strip(' "\''))


# BigQuery schema configurations for all tables to backfill
TABLE_CONFIGS = {
    "customers": {
        "postgres_table": "warehouse.customers",
        "bq_table": "customers",
        "order_by": "customer_id",
        "schema": [
            bigquery.SchemaField("customer_id", "INTEGER"),
            bigquery.SchemaField("name", "STRING"),
            bigquery.SchemaField("email", "STRING"),
            bigquery.SchemaField("country", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
        ]
    },
    "products": {
        "postgres_table": "warehouse.products",
        "bq_table": "products",
        "order_by": "product_id",
        "schema": [
            bigquery.SchemaField("product_id", "INTEGER"),
            bigquery.SchemaField("name", "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("price", "NUMERIC"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ]
    },
    "orders": {
        "postgres_table": "warehouse.orders",
        "bq_table": "orders",
        "order_by": "created_at",
        "schema": [
            bigquery.SchemaField("order_id", "INTEGER"),
            bigquery.SchemaField("customer_id", "INTEGER"),
            bigquery.SchemaField("product_id", "INTEGER"),
            bigquery.SchemaField("order_date", "TIMESTAMP"),
            bigquery.SchemaField("quantity", "INTEGER"),
            bigquery.SchemaField("unit_price", "NUMERIC"),
            bigquery.SchemaField("total_amount", "NUMERIC"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("processed_at", "TIMESTAMP"),
        ]
    },
    "order_events": {
        "postgres_table": "warehouse.order_events",
        "bq_table": "order_events",
        "order_by": "received_at",
        "schema": [
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
    },
    "quarantine_events": {
        "postgres_table": "warehouse.quarantine_events",
        "bq_table": "quarantine_events",
        "order_by": "quarantined_at",
        "schema": [
            bigquery.SchemaField("quarantine_id", "INTEGER"),
            bigquery.SchemaField("order_id", "INTEGER"),
            bigquery.SchemaField("customer_id", "INTEGER"),
            bigquery.SchemaField("product_id", "INTEGER"),
            bigquery.SchemaField("quantity", "INTEGER"),
            bigquery.SchemaField("amount", "NUMERIC"),
            bigquery.SchemaField("event_type", "STRING"),
            bigquery.SchemaField("event_timestamp", "TIMESTAMP"),
            bigquery.SchemaField("error_message", "STRING"),
            bigquery.SchemaField("quarantined_at", "TIMESTAMP"),
            bigquery.SchemaField("resolved", "BOOLEAN"),
        ]
    },
    "permanent_failures": {
        "postgres_table": "warehouse.permanent_failures",
        "bq_table": "permanent_failures",
        "order_by": "failed_at",
        "schema": [
            bigquery.SchemaField("failure_id", "INTEGER"),
            bigquery.SchemaField("order_id", "INTEGER"),
            bigquery.SchemaField("customer_id", "INTEGER"),
            bigquery.SchemaField("product_id", "INTEGER"),
            bigquery.SchemaField("quantity", "INTEGER"),
            bigquery.SchemaField("amount", "NUMERIC"),
            bigquery.SchemaField("event_type", "STRING"),
            bigquery.SchemaField("event_timestamp", "TIMESTAMP"),
            bigquery.SchemaField("error_message", "STRING"),
            bigquery.SchemaField("failed_at", "TIMESTAMP"),
            bigquery.SchemaField("retry_count", "INTEGER"),
        ]
    },
    "quality_report": {
        "postgres_table": "warehouse.quality_report",
        "bq_table": "quality_report",
        "order_by": "created_at",
        "schema": [
            bigquery.SchemaField("report_id", "INTEGER"),
            bigquery.SchemaField("pipeline_name", "STRING"),
            bigquery.SchemaField("start_time", "TIMESTAMP"),
            bigquery.SchemaField("end_time", "TIMESTAMP"),
            bigquery.SchemaField("total_records", "INTEGER"),
            bigquery.SchemaField("valid_records", "INTEGER"),
            bigquery.SchemaField("quarantined_records", "INTEGER"),
            bigquery.SchemaField("error_rate", "NUMERIC"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ]
    },
    "pipeline_execution": {
        "postgres_table": "warehouse.pipeline_execution",
        "bq_table": "pipeline_execution",
        "order_by": "created_at",
        "schema": [
            bigquery.SchemaField("execution_id", "INTEGER"),
            bigquery.SchemaField("pipeline_name", "STRING"),
            bigquery.SchemaField("start_time", "TIMESTAMP"),
            bigquery.SchemaField("end_time", "TIMESTAMP"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("rows_processed", "INTEGER"),
            bigquery.SchemaField("error_message", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ]
    }
}


def backfill():
    load_env_vars()
    
    # Target GCP configurations
    gcp_project = os.getenv("GCP_PROJECT_ID")
    if not gcp_project:
        print("Error: GCP_PROJECT_ID environment variable is not set.")
        sys.exit(1)
        
    bq_dataset = "nebula_raw_zone"
    
    # Postgres configurations
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "dataware")
    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    print("=" * 60)
    print("🚀 Starting Multi-Table Historical Backfill to BigQuery...")
    print(f"Postgres Source: {pg_host}:{pg_port}/{pg_db}")
    print(f"BigQuery Destination Dataset: {gcp_project}.{bq_dataset}")
    print("=" * 60)
    
    # Initialize PG Connection
    try:
        pg_conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            database=pg_db,
            user=pg_user,
            password=pg_password
        )
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        sys.exit(1)
        
    # Initialize GCP Client
    try:
        bq_client = bigquery.Client(project=gcp_project)
    except Exception as e:
        print(f"Failed to initialize GCP client: {e}")
        print("Please check your Application Default Credentials (ADC) auth status.")
        pg_conn.close()
        sys.exit(1)
        
    # Ensure BigQuery raw dataset exists
    try:
        bq_client.get_dataset(bq_dataset)
    except Exception:
        print(f"Dataset '{bq_dataset}' not found. Creating it...")
        dataset = bigquery.Dataset(f"{gcp_project}.{bq_dataset}")
        dataset.location = "US"
        bq_client.create_dataset(dataset, timeout=30)

    cursor = pg_conn.cursor()
    
    # Loop over each table config and perform the backfill
    for table_name, config in TABLE_CONFIGS.items():
        pg_table = config["postgres_table"]
        bq_table = config["bq_table"]
        order_by = config["order_by"]
        schema = config["schema"]
        
        print(f"\n--- Processing Table: {pg_table} -> {bq_table} ---")
        
        # Get count of rows in PostgreSQL
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {pg_table};")
            total_rows = cursor.fetchone()[0]
            print(f"Rows found in PostgreSQL: {total_rows}")
        except Exception as e:
            print(f"Skipping table '{pg_table}'. Error querying table: {e}")
            pg_conn.rollback()
            continue
            
        # Ensure BigQuery table exists
        table_ref = f"{gcp_project}.{bq_dataset}.{bq_table}"
        try:
            bq_client.get_table(table_ref)
        except Exception:
            print(f"Table '{bq_table}' not found in BQ. Creating it...")
            table = bigquery.Table(table_ref, schema=schema)
            bq_client.create_table(table)
            
        if total_rows == 0:
            print(f"No rows found in {pg_table} to sync.")
            continue
            
        # Chunk configuration
        chunk_size = 50000
        offset = 0
        batch_num = 1
        
        # We use WRITE_TRUNCATE on the very first batch to ensure a clean overwrite backfill,
        # then append subsequent chunks.
        write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        
        # Fetch columns list
        cursor.execute(f"SELECT * FROM {pg_table} LIMIT 0;")
        columns = [desc[0] for desc in cursor.description]
        cols_str = ", ".join(columns)
        
        while offset < total_rows:
            print(f"📦 Syncing batch #{batch_num} (Offset: {offset}, Size: {chunk_size})...")
            
            # Fetch chunk from PostgreSQL
            cursor.execute(f"""
                SELECT {cols_str}
                FROM {pg_table}
                ORDER BY {order_by} ASC
                LIMIT {chunk_size} OFFSET {offset};
            """)
            rows = cursor.fetchall()
            
            if not rows:
                break
                
            # Write to temporary local JSONL file
            temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            for row in rows:
                record = dict(zip(columns, row))
                for k, v in record.items():
                    if isinstance(v, datetime):
                        record[k] = v.isoformat()
                    elif isinstance(v, Decimal):
                        record[k] = float(v)
                temp_file.write(json.dumps(record) + "\n")
            temp_file.close()
            
            # Load into BigQuery
            with open(temp_file.name, "rb") as source_file:
                job_config = bigquery.LoadJobConfig(
                    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                    write_disposition=write_disposition,
                    schema=schema
                )
                load_job = bq_client.load_table_from_file(source_file, table_ref, job_config=job_config)
                load_job.result()
                
            print(f"   Loaded batch #{batch_num} ({len(rows)} rows) into BigQuery.")
            
            # Cleanup temp file
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
                
            offset += len(rows)
            batch_num += 1
            # Subsequent batches should always append
            write_disposition = bigquery.WriteDisposition.WRITE_APPEND

    cursor.close()
    pg_conn.close()
    print("\n✅ Multi-table historical backfill sync successfully completed!")
    print("=" * 60)


if __name__ == "__main__":
    backfill()
