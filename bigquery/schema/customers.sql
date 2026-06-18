-- BigQuery nebula_raw_zone.customers Schema Definition
CREATE TABLE IF NOT EXISTS `nebula_raw_zone.customers` (
    customer_id INT64,
    name STRING,
    email STRING,
    country STRING,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
