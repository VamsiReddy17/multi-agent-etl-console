-- BigQuery nebula_raw_zone.orders Schema Definition
CREATE TABLE IF NOT EXISTS `nebula_raw_zone.orders` (
    order_id INT64,
    customer_id INT64,
    product_id INT64,
    order_date TIMESTAMP,
    quantity INT64,
    unit_price NUMERIC,
    total_amount NUMERIC,
    status STRING,
    created_at TIMESTAMP,
    processed_at TIMESTAMP
);
