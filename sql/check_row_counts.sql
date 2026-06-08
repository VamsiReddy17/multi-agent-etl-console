-- ==============================================================================
-- SQL Script: Check Row Counts of All Data Warehouse Tables
-- ==============================================================================
--
-- Description: 
--   Queries all dimension, fact, streaming events, and audit logs tables 
--   in the warehouse schema and aggregates their row counts into a single list.
--
-- How to run this script:
--   docker exec -it prod_postgres psql -U postgres -d dataware -f /app/sql/check_row_counts.sql
--
-- ==============================================================================

SELECT 
    'warehouse.order_events (Kafka Stream)' AS table_name, 
    COUNT(*) AS row_count 
FROM warehouse.order_events

UNION ALL

SELECT 
    'warehouse.orders (Fact)' AS table_name, 
    COUNT(*) AS row_count 
FROM warehouse.orders

UNION ALL

SELECT 
    'warehouse.pipeline_execution (Audit Logs)' AS table_name, 
    COUNT(*) AS row_count 
FROM warehouse.pipeline_execution

UNION ALL

SELECT 
    'warehouse.customers (Dimension)' AS table_name, 
    COUNT(*) AS row_count 
FROM warehouse.customers

UNION ALL

SELECT 
    'warehouse.products (Dimension)' AS table_name, 
    COUNT(*) AS row_count 
FROM warehouse.products

ORDER BY row_count DESC;
