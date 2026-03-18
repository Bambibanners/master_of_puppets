-- Phase 31: Environment Tags — add env_tag to nodes, jobs, scheduled_jobs
-- Run on existing Postgres deployments. Fresh deployments: create_all handles this automatically.

ALTER TABLE nodes ADD COLUMN IF NOT EXISTS env_tag VARCHAR(32);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS env_tag VARCHAR(32);
ALTER TABLE scheduled_jobs ADD COLUMN IF NOT EXISTS env_tag VARCHAR(32);
