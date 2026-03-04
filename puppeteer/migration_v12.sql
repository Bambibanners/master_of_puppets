-- Phase 3: Service Principals

CREATE TABLE IF NOT EXISTS service_principals (
    id VARCHAR PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    description TEXT,
    role VARCHAR NOT NULL DEFAULT 'operator',
    client_id VARCHAR UNIQUE NOT NULL,
    client_secret_hash VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR NOT NULL,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_service_principals_client_id ON service_principals(client_id);
CREATE INDEX IF NOT EXISTS idx_service_principals_name ON service_principals(name);
