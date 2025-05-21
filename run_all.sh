#!/bin/bash
#chmod +x run_all.sh
#./run_all.sh

set -e
echo "Waiting for PostgreSQL..."
until nc -z postgres 5432; do
  echo "Still waiting for postgres:5432..."
  sleep 2
done
echo "Postgres is ready"

echo "Starting run_all.sh"

export PYTHONPATH=$PYTHONPATH:/app

#echo "Applying migrations..."
#alembic upgrade head
#echo "Migration done"
#
#echo "Filling DB..."
#make filldb_users
#make filldb_pets
#make filldb_reports
#echo "Filling DB done"

echo "Starting App..."
make run_app