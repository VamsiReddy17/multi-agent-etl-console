-- Create Airflow database if not exists (PostgreSQL-compatible syntax)
SELECT 'CREATE DATABASE airflow' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

-- Data Warehouse Schema
CREATE SCHEMA IF NOT EXISTS warehouse;

-- Customers Dimension Table
CREATE TABLE warehouse.customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products Dimension Table
CREATE TABLE warehouse.products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders Fact Table
CREATE TABLE warehouse.orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES warehouse.customers(customer_id),
    product_id INTEGER REFERENCES warehouse.products(product_id),
    order_date TIMESTAMP,
    quantity INTEGER,
    unit_price DECIMAL(10, 2),
    total_amount DECIMAL(12, 2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Order Events (from Kafka stream)
CREATE TABLE warehouse.order_events (
    event_id SERIAL PRIMARY KEY,
    order_id INTEGER,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    amount DECIMAL(12, 2),
    event_type VARCHAR(50),
    event_timestamp TIMESTAMP,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- Pipeline Execution Log
CREATE TABLE warehouse.pipeline_execution (
    execution_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50),
    rows_processed INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quarantine Events Table (DLQ)
CREATE TABLE warehouse.quarantine_events (
    quarantine_id SERIAL PRIMARY KEY,
    order_id INTEGER,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    amount DECIMAL(12, 2),
    event_type VARCHAR(50),
    event_timestamp TIMESTAMP,
    error_message TEXT,
    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE
);

-- Schema Drift Logs Table
CREATE TABLE warehouse.schema_drift_logs (
    drift_id SERIAL PRIMARY KEY,
    drift_type VARCHAR(100),
    field_name VARCHAR(100),
    detected_by VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Logged',
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_orders_customer ON warehouse.orders(customer_id);
CREATE INDEX idx_orders_date ON warehouse.orders(order_date);
CREATE INDEX idx_order_events_processed ON warehouse.order_events(processed);
CREATE INDEX idx_pipeline_exec_status ON warehouse.pipeline_execution(status);

-- Sample Data
INSERT INTO warehouse.customers (name, email, country) VALUES
    ('Alice Johnson', 'alice@example.com', 'USA'),
    ('Bob Smith', 'bob@example.com', 'UK'),
    ('Charlie Brown', 'charlie@example.com', 'Canada'),
    ('Diana Prince', 'diana@example.com', 'USA'),
    ('Eve Wilson', 'eve@example.com', 'Australia');

INSERT INTO warehouse.products (name, category, price) VALUES
    ('Laptop', 'Electronics', 999.99),
    ('Mouse', 'Electronics', 29.99),
    ('Keyboard', 'Electronics', 79.99),
    ('Monitor', 'Electronics', 299.99),
    ('Desk Chair', 'Furniture', 199.99);

INSERT INTO warehouse.orders (customer_id, product_id, order_date, quantity, unit_price, total_amount, status) VALUES
    (1, 1, NOW() - INTERVAL '1 day', 1, 999.99, 999.99, 'completed'),
    (2, 2, NOW() - INTERVAL '2 days', 2, 29.99, 59.98, 'completed'),
    (3, 3, NOW() - INTERVAL '3 days', 1, 79.99, 79.99, 'pending'),
    (1, 4, NOW() - INTERVAL '4 days', 1, 299.99, 299.99, 'completed'),
    (4, 5, NOW() - INTERVAL '5 days', 1, 199.99, 199.99, 'pending');

-- Quality Report Table
CREATE TABLE IF NOT EXISTS warehouse.quality_report (
    report_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_records INTEGER,
    valid_records INTEGER,
    quarantined_records INTEGER,
    error_rate DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Permanent Failures Table
CREATE TABLE IF NOT EXISTS warehouse.permanent_failures (
    failure_id SERIAL PRIMARY KEY,
    order_id INTEGER,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    amount DECIMAL(12, 2),
    event_type VARCHAR(50),
    event_timestamp TIMESTAMP,
    error_message TEXT,
    failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER
);

-- Create indexes
CREATE INDEX idx_permanent_failures_order ON warehouse.permanent_failures(order_id);

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA warehouse TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO postgres;

