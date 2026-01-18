# Feature Context: SMB Mounts & Environment Injection

**Implemented:** 2026-01-18
**Pattern:** Environment Variable Passthrough (Infrastructure-as-Code)

## Overview
We have implemented a mechanism to allow Linux-based Podman Nodes to access Windows SMB/CIFS shares that are accessible to the Host OS, *without* hardcoding credentials or modifying signed code.

## The Architecture
1.  **Host-Identity (DrvFS)**:
    *   The Windows Host authenticates to SMB shares (AD/Kerberos) as usual.
    *   The Installer (`install_node.ps1`) mounts these paths into the Podman VM using `type=drvfs`.
    *   The Node Container binds these paths via `node-compose.yaml`.

2.  **Environment Injection**:
    *   The Installer/Server logic sanitizes the input mount source (e.g., `\\finance\data`) into an Environment Variable Key (e.g., `MOUNT_FINANCE_DATA`).
    *   The Container receives this variable pointing to the internal Linux path (e.g., `/mnt/smm/finance/data`).

## Usage Rule for Agents/Devs
When writing Python scripts for this system, **NEVER** hardcode Windows paths if they refer to network resources.

**INCORRECT**:
```python
# Fails on Linux Node
path = r"\\finance\data\results.csv"
```

**CORRECT**:
```python
import os
# Portable Pattern
# 1. Tries to get the Linux path from Env (Container execution)
# 2. Falls back to the Windows path (Local Host execution/testing)
root = os.getenv("MOUNT_FINANCE_DATA", r"\\finance\data")
path = os.path.join(root, "results.csv")
```

## Troubleshooting
*   **Missing Mounts**: Check `install_node.ps1` output. The `podman machine ssh` steps must succeed.
*   **Logs**: The Node prints all active `MOUNT_*` keys on startup. Use `docker logs <node_id>` to verify injection.
