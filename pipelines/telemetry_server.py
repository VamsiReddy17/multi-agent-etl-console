import os
import json
import logging
import asyncio
import psycopg2
from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telemetry_server")

app = FastAPI(title="GCP Pipeline Console Telemetry Gateway")

# Enable CORS for the dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipelines", "streaming_etl.log")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres_password"),
            dbname=os.getenv("POSTGRES_DB", "dataware")
        )
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return None

def fetch_db_records() -> Dict[str, List[Dict[str, Any]]]:
    conn = get_db_connection()
    if not conn:
        return {
            'warehouse.order_events': [],
            'warehouse.orders': [],
            'warehouse.pipeline_execution': [],
            'warehouse.schema_drift_logs': []
        }
    records = {
        'warehouse.order_events': [],
        'warehouse.orders': [],
        'warehouse.pipeline_execution': [],
        'warehouse.schema_drift_logs': []
    }
    try:
        with conn.cursor() as cur:
            # 1. order_events
            cur.execute("""
                SELECT event_id, customer_id, amount, processed, event_timestamp 
                FROM warehouse.order_events 
                ORDER BY event_id DESC LIMIT 5;
            """)
            for row in cur.fetchall():
                records['warehouse.order_events'].append({
                    "id": f"evt_{row[0]}",
                    "customer": f"cust_{row[1]}" if row[1] else "—",
                    "total": f"${float(row[2]):.2f}" if row[2] is not None else "$0.00",
                    "status": "Passed" if row[3] else "Pending",
                    "time": row[4].strftime("%H:%M:%S") if row[4] else "—"
                })

            # 2. orders
            cur.execute("""
                SELECT o.order_id, c.name, o.total_amount, o.status, o.order_date 
                FROM warehouse.orders o
                LEFT JOIN warehouse.customers c ON o.customer_id = c.customer_id
                ORDER BY o.order_id DESC LIMIT 5;
            """)
            for row in cur.fetchall():
                records['warehouse.orders'].append({
                    "id": f"ord_{row[0]}",
                    "customer": row[1] or "Unknown",
                    "total": f"${float(row[2]):.2f}" if row[2] is not None else "$0.00",
                    "status": row[3].capitalize() if row[3] else "Pending",
                    "time": row[4].strftime("%H:%M:%S") if row[4] else "—"
                })

            # 3. pipeline_execution
            cur.execute("""
                SELECT execution_id, pipeline_name, status, rows_processed, start_time, end_time 
                FROM warehouse.pipeline_execution 
                ORDER BY execution_id DESC LIMIT 5;
            """)
            for row in cur.fetchall():
                latency_ms = 0
                if row[4] and row[5]:
                    latency_ms = int((row[5] - row[4]).total_seconds() * 1000)
                records['warehouse.pipeline_execution'].append({
                    "id": f"run_{row[0]}",
                    "dag": row[1] or "streaming_ingestion",
                    "tasks": "4/4" if row[2] == "success" else "3/4",
                    "state": row[2].capitalize() if row[2] else "Unknown",
                    "latency": f"{latency_ms}ms"
                })

            # 4. schema_drift_logs
            cur.execute("""
                SELECT drift_id, drift_type, field_name, detected_by, status, logged_at 
                FROM warehouse.schema_drift_logs 
                ORDER BY drift_id DESC LIMIT 5;
            """)
            for row in cur.fetchall():
                records['warehouse.schema_drift_logs'].append({
                    "id": f"drift_{row[0]}",
                    "type": row[1] or "Schema Drift Warning",
                    "field": row[2] or "—",
                    "agent": row[3] or "QualityAgent",
                    "status": row[4] or "Logged",
                    "time": row[5].strftime("%H:%M:%S") if row[5] else "—"
                })
    except Exception as e:
        logger.error(f"Error fetching DB records: {e}")
    finally:
        conn.close()
    return records

def fetch_quarantine_records() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []
    records = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT quarantine_id, order_id, customer_id, product_id, quantity, amount, event_type, event_timestamp, error_message, quarantined_at, resolved
                FROM warehouse.quarantine_events
                WHERE resolved = FALSE
                ORDER BY quarantine_id DESC LIMIT 20;
            """)
            for row in cur.fetchall():
                payload_dict = {
                    "order_id": row[1],
                    "customer_id": row[2],
                    "product_id": row[3],
                    "quantity": row[4],
                    "amount": float(row[5]) if row[5] is not None else 0.0,
                    "event_type": row[6],
                    "event_timestamp": row[7].isoformat() if row[7] else None
                }
                records.append({
                    "id": f"REC-{row[0]}",
                    "timestamp": row[9].strftime("%H:%M:%S") if row[9] else "—",
                    "agent": "QualityAgent",
                    "error": row[8] or "Validation Failure",
                    "payload": json.dumps(payload_dict, indent=2)
                })
    except Exception as e:
        logger.error(f"Error fetching quarantine records: {e}")
    finally:
        conn.close()
    return records

def fetch_metrics() -> Dict[str, Any]:
    conn = get_db_connection()
    metrics = {
        "totalRuns": 0,
        "successRuns": 0,
        "processedIngest": 0,
        "processedLoad": 0,
        "quarantined": 0,
        "quarantineRate": 0.0,
        "loadedCount": 0,
        "ingestRate": 250,
        "avgLatency": 0.0,
        "stageDurations": {
            "ingestion": 0.12,
            "transform": 0.02,
            "quality": 0.01,
            "load": 0.15
        }
    }
    if not conn:
        return metrics
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*), COUNT(CASE WHEN status = 'success' THEN 1 END) FROM warehouse.pipeline_execution;")
            total_runs, success_runs = cur.fetchone()
            metrics["totalRuns"] = total_runs or 0
            metrics["successRuns"] = success_runs or 0

            cur.execute("SELECT COALESCE(SUM(rows_processed), 0) FROM warehouse.pipeline_execution;")
            sum_rows = cur.fetchone()[0]
            metrics["processedLoad"] = sum_rows or 0
            metrics["loadedCount"] = sum_rows or 0

            cur.execute("SELECT COUNT(*) FROM warehouse.quarantine_events;")
            quarantined_count = cur.fetchone()[0] or 0
            metrics["quarantined"] = quarantined_count
            metrics["processedIngest"] = metrics["processedLoad"] + quarantined_count
            
            total = metrics["processedIngest"]
            if total > 0:
                metrics["quarantineRate"] = round((quarantined_count / total) * 100, 2)
            
            cur.execute("SELECT AVG(EXTRACT(EPOCH FROM (end_time - start_time)) * 1000) FROM warehouse.pipeline_execution WHERE end_time IS NOT NULL;")
            avg_lat = cur.fetchone()[0]
            metrics["avgLatency"] = round(float(avg_lat), 1) if avg_lat is not None else 0.0

    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
    finally:
        conn.close()
    return metrics

def read_tail_logs() -> List[Dict[str, Any]]:
    formatted_logs = []
    if not os.path.exists(LOG_FILE_PATH):
        # Fallback logs when log file hasn't been created yet
        return [
            { "id": 1, "type": "info", "text": "Initializing Multi-Agent Telemetry Socket Gateway..." },
            { "id": 2, "type": "success", "text": "Connected to PostgreSQL Data Warehouse." },
            { "id": 3, "type": "info", "text": "Waiting for background ETL streaming processes..." }
        ]
    
    try:
        with open(LOG_FILE_PATH, "r") as f:
            lines = f.readlines()
            last_lines = lines[-50:]
            for idx, line in enumerate(last_lines):
                line_str = line.strip()
                if not line_str:
                    continue
                
                log_type = "info"
                if "[WARNING]" in line_str or "warning" in line_str.lower() or "⚠" in line_str:
                    log_type = "warning"
                elif "[ERROR]" in line_str or "error" in line_str.lower() or "✗" in line_str:
                    log_type = "error"
                elif "[SUCCESS]" in line_str or "success" in line_str.lower() or "✓" in line_str or "passed" in line_str.lower():
                    log_type = "success"
                
                formatted_logs.append({
                    "id": idx + 100,
                    "type": log_type,
                    "text": line_str
                })
    except Exception as e:
        logger.error(f"Error reading tail logs: {e}")
    
    return formatted_logs

class ReprocessRequest(BaseModel):
    quarantine_id: str
    payload: Dict[str, Any]

@app.post("/reprocess")
def reprocess_event(req: ReprocessRequest):
    # Parse quarantine_id (REC-XYZ -> XYZ)
    qid_str = req.quarantine_id
    if qid_str.startswith("REC-"):
        qid_str = qid_str[4:]
    try:
        quarantine_id = int(qid_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid quarantine record ID format.")

    payload = req.payload
    
    # 1. Validation Logic
    errors = []
    for field in ["order_id", "customer_id", "amount"]:
        if payload.get(field) is None:
            errors.append(f"Missing required field: '{field}'")
    
    if not errors:
        amount = payload.get("amount", payload.get("total_amount", 0))
        try:
            amount = float(amount)
            if amount <= 0:
                errors.append(f"Amount must be > 0, got {amount}")
        except (ValueError, TypeError):
            errors.append(f"Invalid amount value: {amount}")

        qty = payload.get("quantity", 1)
        try:
            qty = int(qty)
            if qty < 1:
                errors.append(f"Quantity must be >= 1, got {qty}")
        except (ValueError, TypeError):
            errors.append(f"Invalid quantity value: {qty}")

        for id_field in ("customer_id", "product_id"):
            val = payload.get(id_field)
            if val is not None:
                try:
                    if int(val) <= 0:
                        errors.append(f"'{id_field}' must be a positive integer, got {val}")
                except (ValueError, TypeError):
                    errors.append(f"'{id_field}' is not a valid integer: {val}")

    if errors:
        raise HTTPException(status_code=400, detail="Verification Failed: " + "; ".join(errors))

    # 2. Database Transaction
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection offline.")
    
    try:
        with conn.cursor() as cur:
            # Remove from quarantine
            cur.execute("DELETE FROM warehouse.quarantine_events WHERE quarantine_id = %s RETURNING quarantine_id;", (quarantine_id,))
            deleted = cur.fetchone()
            if not deleted:
                conn.rollback()
                raise HTTPException(status_code=404, detail="Quarantine record not found or already reprocessed.")
            
            # Insert into order_events
            cur.execute(
                """
                INSERT INTO warehouse.order_events
                    (order_id, customer_id, product_id, quantity, amount, event_type, event_timestamp, received_at, processed)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, NOW(), FALSE);
                """,
                (
                    payload.get("order_id"),
                    payload.get("customer_id"),
                    payload.get("product_id"),
                    payload.get("quantity", 1),
                    payload.get("amount") or payload.get("total_amount") or 0.0,
                    payload.get("event_type", "order_placed"),
                    payload.get("event_timestamp", datetime.now().isoformat())
                )
            )
        conn.commit()
        logger.info(f"Successfully reprocessed quarantine ID: {quarantine_id}")
        return {"status": "success", "message": f"Record {req.quarantine_id} reprocessed successfully."}
    except HTTPException as he:
        raise he
    except Exception as e:
        conn.rollback()
        logger.error(f"Reprocessing transaction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database transaction failed: {e}")
    finally:
        conn.close()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("New dashboard WebSocket client connected!")
    try:
        while True:
            # Aggregated stream data
            metrics_data = fetch_metrics()
            logs_data = read_tail_logs()
            quarantine_data = fetch_quarantine_records()
            db_records_data = fetch_db_records()
            
            payload = {
                "metrics": metrics_data,
                "logs": logs_data,
                "quarantine": quarantine_data,
                "db_records": db_records_data
            }
            
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket execution error: {e}")

if __name__ == "__main__":
    import uvicorn
    # Start the server with hot reloading
    uvicorn.run("telemetry_server:app", host="0.0.0.0", port=8085, reload=True)
