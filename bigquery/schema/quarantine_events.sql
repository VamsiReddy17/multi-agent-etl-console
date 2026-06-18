-- BigQuery nebula_raw_zone.quarantine_events Schema Definition
CREATE TABLE IF NOT EXISTS `nebula_raw_zone.quarantine_events` (
    quarantine_id INT64,
    order_id INT64,
    customer_id INT64,
    product_id INT64,
    quantity INT64,
    amount NUMERIC,
    event_type STRING,
    event_timestamp TIMESTAMP,
    error_message STRING,
    quarantined_at TIMESTAMP,
    resolved BOOLEAN
);
