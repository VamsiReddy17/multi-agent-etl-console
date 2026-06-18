-- BigQuery nebula_raw_zone.quality_report Schema Definition
CREATE TABLE IF NOT EXISTS `nebula_raw_zone.quality_report` (
    report_id INT64,
    pipeline_name STRING,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_records INT64,
    valid_records INT64,
    quarantined_records INT64,
    error_rate NUMERIC,
    created_at TIMESTAMP
);
