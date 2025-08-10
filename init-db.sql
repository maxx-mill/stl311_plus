-- Initialize PostgreSQL database with PostGIS extension
-- This script runs when the PostgreSQL container starts

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create database user (optional)
-- CREATE USER postgres WITH PASSWORD 'password';
--GRANT ALL PRIVILEGES ON DATABASE stl311_db TO postgres;

-- Create spatial indexes for better performance
-- (These will be created automatically by GeoAlchemy2, but we can add custom ones here)

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres; 