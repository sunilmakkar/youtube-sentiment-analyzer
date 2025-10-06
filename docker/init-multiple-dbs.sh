#!/bin/bash
set -e

# Create test database alongside main
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE ytsa_test;
EOSQL
