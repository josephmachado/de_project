#!/bin/bash
set -e

# cd into airflow home directory
cd /home/airflow

# Start Airflow in the background
uv run airflow standalone &

# Start Jupyter Lab in the foreground
exec uv run jupyter lab --allow-root --ip=0.0.0.0 --no-browser --IdentityProvider.token=''
