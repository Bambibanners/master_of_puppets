-- Phase 32: operator_env_tag flag on nodes
-- Marks env_tag as operator-set so node heartbeats cannot overwrite it.
-- Fresh deployments: create_all handles this automatically.
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS operator_env_tag BOOLEAN NOT NULL DEFAULT FALSE;
