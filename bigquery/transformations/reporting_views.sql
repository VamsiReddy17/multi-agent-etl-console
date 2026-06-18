-- BigQuery Reporting View transformations
CREATE OR REPLACE VIEW `solar_core_analytics.orders_reporting` AS (
    SELECT 
        order_id,
        customer_id,
        product_id,
        quantity,
        amount,
        event_timestamp,
        received_at
    FROM 
        `nebula_raw_zone.order_events`
);

