#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Set default database name if not provided
export NAMU_DB=${NAMU_DB:-wiki_db}

# Create database configuration if it doesn't exist
if [ ! -f "data/postgresql.json" ]; then
    echo "Creating PostgreSQL configuration..."
    mkdir -p data
    cat > data/postgresql.json << EOF
{
    "user": "${NAMU_POSTGRESQL_USER}",
    "password": "${NAMU_POSTGRESQL_PASSWORD}",
    "host": "${NAMU_POSTGRESQL_HOST}",
    "port": "${NAMU_POSTGRESQL_PORT}"
}
EOF
fi

# Create set.json configuration if it doesn't exist
if [ ! -f "data/set.json" ]; then
    echo "Creating set.json configuration..."
    cat > data/set.json << EOF
{
    "db_type": "postgresql",
    "db": "${NAMU_DB}"
}
EOF
fi

# Start the application
echo "Starting openNAMU..."
python app.py