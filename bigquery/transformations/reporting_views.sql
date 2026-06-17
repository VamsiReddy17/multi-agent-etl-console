-- BigQuery Reporting View transformations
CREATE OR REPLACE VIEW `warehouse.orders_reporting` AS (
    SELECT 
        order_id,
        customer_id,
        product_id,
        quantity,
        amount,
        event_timestamp,
        received_at
    FROM 
        `raw.order_events`
);

