# Milestone 6: Remote Environment Validation

## Objective
Validate the Master of Puppets architecture in a true remote networking context. Move beyond `localhost` to ensure the security model, installer, and connectivity hold up when deployed across different Linux hosts.

## Context
The project has been developed and tested primarily in a local-loopback environment using Docker/Podman on a single machine. While this proves the logic, it doesn't fully test:
1.  **mTLS across IPs**: Certificates issued for `localhost` won't work for remote IPs unless SANs (Subject Alternative Names) are correctly set.
2.  **Caddy Reverse Proxy**: The current `compose.server.yaml` and `Caddyfile` need validation on a real Linux host with a public/private IP.
3.  **Bootstrap Flow**: New nodes must download the CA over plain HTTP (port 80) before they can trust the HTTPS (port 443) API.

## Core Requirements (v2 Hardening)
- **REM-01**: Server stack can be deployed on a remote Linux host with a single command/script.
- **REM-02**: `SERVER_HOSTNAME` correctly updates Caddy's TLS configuration to include the remote IP/FQDN.
- **REM-03**: Linux Universal Installer (`install_universal.sh`) works on fresh Debian/Ubuntu environments without pre-installed dependencies.

## Strategy
1.  **Phase 1**: Remote Server Deployment. Create a `deploy_server.sh` script and validate the Caddy/Postgres/Agent stack.
2.  **Phase 2**: Linux Universal Installer. Refine `install_universal.sh` for maximum portability and automatic dependency resolution (jq, curl, docker/podman).
3.  **Phase 3**: End-to-End Validation. Perform a full "Enroll -> Heartbeat -> Job -> Result" cycle between two physically separate Linux instances.
