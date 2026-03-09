# Plan 06-01 Summary: Remote Infrastructure Hardening

**Status:** Complete
**Date:** 2026-03-06

## Actions Taken
- **CA Unification**: Modified `PKIService` to detect and use the global `cert-manager` (Caddy) root CA if available. This ensures nodes only need to trust a single CA for both HTTPS and mTLS.
- **Server Deployment Automation**: Created `puppeteer/installer/deploy_server.sh` to automate Docker/Compose installation, `.env` initialization, and stack launching on remote Linux.
- **Installer Hardening**: Updated `puppeteer/installer/install_universal.sh` with:
    *   `install_ca()`: Automatically adds the MOP Root CA to the system trust store (Debian/Ubuntu/RHEL) when run with sudo.
    *   Improved `SERVER_URL` handling to respect `SERVER_HOSTNAME`.
- **Documentation**: Created `docs/REMOTE_DEPLOYMENT.md` providing a clear, end-to-end guide for setting up the platform in a multi-host environment.

## Verification Results
- `PKIService` correctly re-maps its paths when `/app/global_certs` is present.
- `deploy_server.sh` generates secure defaults and handles hostname propagation.
- `install_universal.sh` logic for CA installation covers both Debian and RHEL families.

## Next Steps
- **Phase 2: Linux Universal Installer Validation**: This phase is largely complete by the hardening above, but we need to verify the "Remote Node" enrollment flow if possible, or move to Phase 3 for end-to-end network validation.
