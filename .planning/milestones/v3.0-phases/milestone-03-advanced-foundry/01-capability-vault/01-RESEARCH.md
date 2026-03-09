# Phase 1: Dynamic Matrix & Artifact Vault - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 1 establishes the foundational data models and services for dynamic capability management and secure artifact hosting. This transition allows the orchestrator to act as a local package repository, reducing reliance on public CDNs and enabling air-gapped node upgrades.

## Existing Capabilities
- **CapabilityMatrix**: A table currently used during Docker image generation. It maps `base_os_family` + `tool_id` to an `injection_recipe` (Dockerfile snippet) and a `validation_cmd`.
- **Static Seeds**: Standard recipes (Python, Node.js, PowerShell) are currently seeded via `main.py` at startup.
- **Artifacts**: None. All dependencies are currently fetched via `apt`, `apk`, or `pip` directly from the internet.

## Requirements Analysis
- **Dynamic CRUD**: Admins must be able to add/edit/delete capability entries via the dashboard.
- **Artifact Vault**: A storage mechanism for binary installers (e.g., `.deb`, `.rpm`, `.ps1`, `.zip`).
- **Secure References**: Capability recipes should be able to reference local artifacts via a stable URL or token.
- **Approved OS Bases**: A central list of supported base images (Debian, Alpine, Ubuntu, Windows) to populate dropdowns in the Foundry.

## Technical Strategy
1. **Database Schema Expansion**:
    - `Artifact`: Metadata for uploaded binary files.
    - `ApprovedOS`: A list of validated base container images.
    - `CapabilityMatrix`: Add `artifact_id` (optional) to link a recipe directly to a file.
2. **File Storage**:
    - Primary: Local filesystem (`/app/vault/`).
    - Metadata: DB-backed tracking including SHA256 for integrity.
3. **API Implementation**:
    - `POST /api/artifacts`: Multipart file upload.
    - `GET /api/artifacts/{id}/download`: Binary stream.
    - `GET/POST/PUT/DELETE /api/capability-matrix`: Full CRUD for recipes.
    - `GET /api/approved-os`: List of supported bases.

## Potential Pitfalls
- **Disk Space**: Large binaries could fill the container's overlay or local volume. Need to monitor `size_bytes`.
- **Permission Bloat**: Recipe management is a high-privilege action (it injects shell commands). Must be restricted to `admin`.
- **Mime-Types**: Ensure installers are served with correct headers so Puppets don't misinterpret them.

---
*Phase: 01-capability-vault*
*Context: Master of Puppets Advanced Foundry Milestone*
