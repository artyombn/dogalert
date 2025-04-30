#!/bin/bash
#chmod +x run_all.sh
#./run_all.sh

set -e

echo "Starting run_all.sh"

#echo "Checking installed packages"
#pip list

echo "Applying migrations..."
alembic upgrade head
echo "Migration done"

echo "Filling DB..."
make filldb_users
make filldb_pets
make filldb_reports
echo "Filling DB done"

echo "Starting FastAPI..."
uvicorn src.web.main:app --host 0.0.0.0 --port 8001 --reload