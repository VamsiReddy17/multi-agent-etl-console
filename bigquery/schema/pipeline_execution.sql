-- BigQuery nebula_raw_zone.pipeline_execution Schema Definition
CREATE TABLE IF NOT EXISTS `nebula_raw_zone.pipeline_execution` (
    execution_id INT64,
    pipeline_name STRING,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status STRING,
    rows_processed INT64,
    error_message STRING,
    created_at TIMESTAMP
);
