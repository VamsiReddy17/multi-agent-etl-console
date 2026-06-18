-- BigQuery nebula_raw_zone.products Schema Definition
CREATE TABLE IF NOT EXISTS `nebula_raw_zone.products` (
    product_id INT64,
    name STRING,
    category STRING,
    price NUMERIC,
    created_at TIMESTAMP
);
