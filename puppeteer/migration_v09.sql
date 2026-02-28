-- Migration for v0.9 Capability-Based Scheduling
-- Run this against your existing 'jobs.db' or Postgres instance.

BEGIN;

-- 1. Add capabilities and node_secret_hash to nodes
ALTER TABLE nodes ADD COLUMN capabilities TEXT;
ALTER TABLE nodes ADD COLUMN node_secret_hash TEXT;

-- 2. Add capability_requirements to jobs
ALTER TABLE jobs ADD COLUMN capability_requirements TEXT;

-- 3. Add capability_requirements to scheduled_jobs
ALTER TABLE scheduled_jobs ADD COLUMN capability_requirements TEXT;

COMMIT;
