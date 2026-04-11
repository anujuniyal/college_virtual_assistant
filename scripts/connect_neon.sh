#!/bin/bash

# Neon Database Connection Script
# Replace these values with your actual Neon database credentials

NEON_HOST="ep-small-tree-anl3swp3-pooler.c-6.us-east-1.aws.neon.tech"
NEON_PORT="5432"
NEON_DATABASE="neondb"
NEON_USER="neondb_owner"
NEON_PASSWORD="npg_vVJ1xS3CwXIf"

# Full psql connection command
echo "Connecting to Neon database..."
echo "Host: $NEON_HOST"
echo "Database: $NEON_DATABASE"
echo "User: $NEON_USER"
echo ""

# Option 1: Interactive connection (will prompt for password)
# psql -h $NEON_HOST -p $NEON_PORT -U $NEON_USER -d $NEON_DATABASE

# Option 2: Connection with password in command (less secure)
PGPASSWORD=$NEON_PASSWORD psql -h $NEON_HOST -p $NEON_PORT -U $NEON_USER -d $NEON_DATABASE

# Option 3: Using connection string
# psql "postgresql://$NEON_USER:$NEON_PASSWORD@$NEON_HOST:$NEON_PORT/$NEON_DATABASE?sslmode=require"
