-- Initialize PostgreSQL database for EduBot development
-- This script runs automatically when the container starts

-- Create additional extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';
