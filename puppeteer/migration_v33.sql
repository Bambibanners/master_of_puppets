-- Phase 30: Runtime Attestation columns on execution_records
-- Safe to run on existing deployments: all columns are nullable
-- Note: SQLite does not support IF NOT EXISTS on ALTER TABLE.
--       For SQLite dev environments, create_all at startup handles new columns.
--       This migration is for existing PostgreSQL deployments only.
ALTER TABLE execution_records ADD COLUMN IF NOT EXISTS attestation_bundle TEXT;
ALTER TABLE execution_records ADD COLUMN IF NOT EXISTS attestation_signature TEXT;
ALTER TABLE execution_records ADD COLUMN IF NOT EXISTS attestation_verified VARCHAR(16);
