# Security Architecture (Zero-Trust)

## Core Principles
1.  **Verify Explicitly**: No entity is trusted by default.
2.  **Least Privilege**: Nodes only access what is explicitly provisioned.
3.  **Assume Breach**: Architecture minimizes blast radius.

## Authentication Mechanisms

### 1. Mutual TLS (mTLS)
*   **What**: Both Puppeteer and the Puppet present certificates to prove their identity.
*   **Why**: Prevents "Rogue Puppets" (unauthorized workers) and "Man-in-the-Middle" attacks.
*   **Implementation**: 
    *   Puppeteer has `server.crt` signed by Internal Root CA.
    *   Puppet has `node-[id].crt` signed by Internal Root CA.
    *   Communication fails if either side cannot validate the other's signature.

### 2. Trust Bootstrapping
*   **Problem**: How does a new Puppet trust Puppeteer without pre-installed secrets?
*   **Solution**: **Embedded Trust Token**.
    *   The `JOIN_TOKEN` is a Base64-encoded blob containing:
        1.  **Auth Token**: For the initial API handshake.
        2.  **Root CA**: The public key of the Trust Authority.
    *   The Puppet decodes this, installs the CA, and *then* connects. This eliminates the need for manual certificate distribution.

### 3. Container Isolation
*   **Filesystem**: Puppets run with a read-only root (conceptually) and ephemeral read-write layer.
*   **Mounts**: Puppets have **NO** bind mounts to the Host OS root. They cannot read `C:\` or `/etc`.
*   **Network**: Puppets communicate strictly outbound to Puppeteer.

## Operational Security
*   **Secrets**: All API Keys and Database credentials are injected via Environment Variables at container startup.
*   **Code Signing**: Scripts must be signed by an authorized Private Key (Ed25519) before execution to prevent RCE tampering.
