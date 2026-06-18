#!/usr/bin/env python3
"""
PostgreSQL to BigQuery Historical Backfill Script

Loads existing order events from PostgreSQL, stages them in GCS,
and imports them into BigQuery in chunked batches.
Uses Google Application Default Credentials (ADC).
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
    # Check if a local .env file exists and parse it manually if python-dotenv is absent
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ.setdefault(key, val.strip(' "\''))


def backfill():
    load_env_vars()
    
    # Target GCP configurations
    gcp_project = os.getenv("GCP_PROJECT_ID")
    if not gcp_project:
        print("Error: GCP_PROJECT_ID environment variable is not set.")
        sys.exit(1)
        
    gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "my-etl-landing-bucket")
    bq_dataset = "nebula_raw_zone"
    bq_table = "order_events"
    
    # Postgres configurations
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "dataware")
    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    print("=" * 60)
    print("🚀 Starting Historical Backfill to BigQuery...")
    print(f"Postgres Source: {pg_host}:{pg_port}/{pg_db}")
    print(f"GCS Destination Bucket: gs://{gcs_bucket_name}")
    print(f"BigQuery Destination Table: {gcp_project}.{bq_dataset}.{bq_table}")
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
        
    # Get total count of rows to backfill
    cursor = pg_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM warehouse.order_events;")
    total_rows = cursor.fetchone()[0]
    print(f"Total rows found in PostgreSQL: {total_rows}")
    
    if total_rows == 0:
        print("No historical rows found to backfill. Exiting.")
        cursor.close()
        pg_conn.close()
        return
        
    # Chunk configuration
    chunk_size = 50000
    offset = 0
    
    # Ensure BigQuery raw dataset exists
    try:
        bq_client.get_dataset(bq_dataset)
    except Exception:
        print(f"Dataset '{bq_dataset}' not found. Creating it...")
        dataset = bigquery.Dataset(f"{gcp_project}.{bq_dataset}")
        dataset.location = "US"
        bq_client.create_dataset(dataset, timeout=30)
        
    # Ensure raw.order_events table exists
    table_ref = f"{gcp_project}.{bq_dataset}.{bq_table}"
    try:
        bq_client.get_table(table_ref)
    except Exception:
        print(f"Table '{bq_table}' not found. Creating it...")
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
        table = bigquery.Table(table_ref, schema=schema)
        bq_client.create_table(table)
        
    # GCS staging bucket is bypassed to support Sandbox accounts without billing
        
    batch_num = 1
    while offset < total_rows:
        print(f"\n📦 Processing batch #{batch_num} (Offset: {offset}, Size: {chunk_size})...")
        
        # 1. Fetch chunk from Postgres
        cursor.execute(f"""
            SELECT 
                event_id, order_id, customer_id, product_id, quantity, amount, 
                event_type, event_timestamp, received_at, processed 
            FROM 
                warehouse.order_events 
            ORDER BY 
                received_at ASC
            LIMIT {chunk_size} OFFSET {offset};
        """)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        if not rows:
            break
            
        # 2. Write to temp JSONL file
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        for row in rows:
            record = dict(zip(columns, row))
            # Convert type formatting
            for k, v in record.items():
                if isinstance(v, datetime):
                    record[k] = v.isoformat()
                elif isinstance(v, Decimal):
                    record[k] = float(v)
            temp_file.write(json.dumps(record) + "\n")
        temp_file.close()
        
        # 3. Load directly to BigQuery from local temp file
        with open(temp_file.name, "rb") as source_file:
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            load_job = bq_client.load_table_from_file(source_file, table_ref, job_config=job_config)
            load_job.result()  # Wait for job execution
        
        print(f"   Successfully loaded batch #{batch_num} ({len(rows)} rows) directly to BigQuery.")
        
        # Cleanup temporary local file
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
            
        offset += len(rows)
        batch_num += 1

    cursor.close()
    pg_conn.close()
    print("\n✅ Historical backfill sync successfully completed!")
    print("=" * 60)


if __name__ == "__main__":
    backfill()
