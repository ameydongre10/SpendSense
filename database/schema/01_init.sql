-- ============================================================
-- SpendSense — Database Initialization
-- 01_init.sql
-- ============================================================
-- This script runs first during PostgreSQL container startup.
-- It creates the spendsense schema and required extensions.
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create application schema
CREATE SCHEMA IF NOT EXISTS spendsense;

-- Set search path
SET search_path TO spendsense, public;

-- Grant usage
GRANT USAGE ON SCHEMA spendsense TO current_user;
