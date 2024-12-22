#!/bin/bash
set -e

psql --username $POSTGRES_USER --dbname $POSTGRES_DB <<-EOSQL
	CREATE DATABASE test_db;
EOSQL