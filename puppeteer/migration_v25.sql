-- migration_v25.sql: Add alerts and webhooks tables
-- Safe for existing deployments; new deployments use create_all

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    type VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    message TEXT NOT NULL,
    resource_id VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR
);

CREATE TABLE IF NOT EXISTS webhooks (
    id SERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    secret VARCHAR NOT NULL,
    events VARCHAR NOT NULL DEFAULT '*',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_failure TIMESTAMP,
    failure_count INTEGER NOT NULL DEFAULT 0
);
