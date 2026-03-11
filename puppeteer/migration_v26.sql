-- migration_v26.sql: Compatibility Engine
-- Adds is_active + runtime_dependencies to capability_matrix.
-- Adds os_family to blueprints (RUNTIME blueprints store their target OS family).
-- Backfills blueprints.os_family = 'DEBIAN' for existing NULL rows.
-- Safe for existing deployments; new deployments use create_all.

ALTER TABLE capability_matrix ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE capability_matrix ADD COLUMN IF NOT EXISTS runtime_dependencies TEXT NOT NULL DEFAULT '[]';

-- Add os_family to blueprints (Phase 11 — stores declared OS family for RUNTIME blueprints)
ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS os_family VARCHAR;

-- Backfill blueprints.os_family for existing NULL rows
-- DEBIAN is the safe default — all current builds are Debian-based
UPDATE blueprints SET os_family = 'DEBIAN' WHERE os_family IS NULL;
