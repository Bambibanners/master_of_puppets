-- migration_v36: Add role column to users table (required for EE RBAC)
-- The role column was removed from CE core in commit bbcb209 but is needed
-- by the EE users/RBAC router. Default 'admin' preserves existing admin user.

ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR NOT NULL DEFAULT 'admin';
