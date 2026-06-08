#!/bin/bash
# Runs the order generator inside the prod_airflow_webserver container
docker exec prod_airflow_webserver python3 /app/scripts/generate_orders.py "$@"
