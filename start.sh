#!/bin/bash
set -e  # Exit on any error

echo "=== openNAMU Deployment Script ==="

# Add local bin to PATH to resolve pip warning
export PATH="/root/.local/bin:$PATH"

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 20

# Set default database name if not provided
export NAMU_DB=${NAMU_DB:-wiki_db}

echo "Environment variables:"
echo "NAMU_POSTGRESQL_HOST: ${NAMU_POSTGRESQL_HOST}"
echo "NAMU_POSTGRESQL_PORT: ${NAMU_POSTGRESQL_PORT}"
echo "NAMU_POSTGRESQL_USER: ${NAMU_POSTGRESQL_USER}"
echo "NAMU_DB: ${NAMU_DB}"
echo "PORT: ${PORT}"

# Create data directory
mkdir -p data
echo "Created data directory"

# Create database configuration if it doesn't exist
if [ ! -f "data/postgresql.json" ]; then
    echo "Creating PostgreSQL configuration..."
    cat > data/postgresql.json << EOF
{
    "user": "${NAMU_POSTGRESQL_USER}",
    "password": "${NAMU_POSTGRESQL_PASSWORD}",
    "host": "${NAMU_POSTGRESQL_HOST}",
    "port": "${NAMU_POSTGRESQL_PORT}"
}
EOF
    echo "PostgreSQL configuration created"
else
    echo "PostgreSQL configuration already exists"
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
    echo "set.json configuration created"
else
    echo "set.json configuration already exists"
fi

# Verify Python and required modules
echo "Python version: $(python --version)"
echo "Checking required modules..."
python -c "import psycopg2; print('psycopg2 available')" || echo "Warning: psycopg2 not available"
python -c "import flask; print('Flask version:', flask.__version__)"
python -c "import hypercorn; print('Hypercorn available')"

# Set the port from Render's PORT environment variable
export NAMU_PORT=${PORT:-10000}
echo "Using port: ${NAMU_PORT}"

# Start the application
echo "Starting openNAMU application..."
exec python app.py