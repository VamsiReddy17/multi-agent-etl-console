-- BigQuery nebula_raw_zone.order_events Schema Definition
CREATE TABLE IF NOT EXISTS `nebula_raw_zone.order_events` (
    event_id INT64,
    order_id INT64,
    customer_id INT64,
    product_id INT64,
    quantity INT64,
    amount NUMERIC,
    event_type STRING,
    event_timestamp TIMESTAMP,
    received_at TIMESTAMP,
    processed BOOL
);
