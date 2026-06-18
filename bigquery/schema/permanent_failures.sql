-- BigQuery nebula_raw_zone.permanent_failures Schema Definition
CREATE TABLE IF NOT EXISTS `nebula_raw_zone.permanent_failures` (
    failure_id INT64,
    order_id INT64,
    customer_id INT64,
    product_id INT64,
    quantity INT64,
    amount NUMERIC,
    event_type STRING,
    event_timestamp TIMESTAMP,
    error_message STRING,
    failed_at TIMESTAMP,
    retry_count INT64
);
