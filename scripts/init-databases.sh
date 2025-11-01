#!/bin/bash
# Initialize PostgreSQL databases for MS2 QBank services
# This script runs automatically when the postgres container starts for the first time

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Create databases for each microservice
    CREATE DATABASE ms2qbank_users;
    CREATE DATABASE ms2qbank_flashcards;
    CREATE DATABASE ms2qbank_assessments;
    CREATE DATABASE ms2qbank_videos;
    CREATE DATABASE ms2qbank_library;
    CREATE DATABASE ms2qbank_planner;
    CREATE DATABASE ms2qbank_reviews;
    CREATE DATABASE ms2qbank_analytics;

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE ms2qbank_users TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE ms2qbank_flashcards TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE ms2qbank_assessments TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE ms2qbank_videos TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE ms2qbank_library TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE ms2qbank_planner TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE ms2qbank_reviews TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE ms2qbank_analytics TO $POSTGRES_USER;
EOSQL

echo "✅ All MS2 QBank databases created successfully!"
