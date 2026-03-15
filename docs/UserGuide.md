# Master of Puppets - User Guide & Wiki

> **Version**: 1.2.0 (Zero-Trust)
> **Role**: Network Orchestration & Automation

## 1. Overview
**Master of Puppets (MoP)** is a secure, containerized orchestration framework designed for executing automation tasks across a distributed network. It prioritizes **Zero-Trust Security**, **Operational Visibility**, and **Ease of Use**.

### Key Concepts
*   **Puppeteer**: The central server (Control Plane) that manages state, jobs, and security.
*   **Puppet**: A lightweight worker (Satellite Node) that executes tasks. Puppets are isolated and reach out to Puppeteer (Pull Model).
*   **Job**: A defined task (e.g., "Run Network Scan") linked to a script.
*   **Signature**: A cryptographic proof that a script is authorized to run.

---

## 2. The Dashboard (Health Centre)
The dashboard is your central control plane (`http://<server-ip>:5173`).

### Health Centre (Puppets)
The **Puppets** view provides a high-density "Network Operations Center" (NOC) oversight.
*   **Status Indicators**:
    *   🟢 **Green Pulse (Online)**: Puppet is checking in regularly (<30s).
    *   🔴 **Red (Offline)**: Puppet has missed heartbeats >30s.
    *   🟡 **Yellow (Busy/Load)**: High CPU request or latency.
*   **Sparklines**: Real-time graphs showing CPU and RAM usage history (5-minute window).
*   **Verified Badge**: Indicates the Puppet has successfully presented a valid mTLS certificate.

### Orchestration (Jobs)
Manage your automation tasks.
*   **Active Jobs**: Watch ongoing executions.
*   **History**: Audit logs of past runs (Exit Codes, Logs).
*   **Schedules**: Define recurring Cron jobs (e.g., `0 2 * * *` for nightly backups).

### Security (Signatures)
*   **Code Signing**: MoP refuses to run unsigned code.
*   **Trusted Keys**: Manage the Ed25519 Public Keys authorized to sign scripts.

---

## 3. Puppet Enrollment (Getting Started)
To add a new worker to the mesh:

1.  **Generate Token**: Go to **Admin** -> **Generate Token**.
    *   *Note*: This token contains the Root CA and a temporary signature. It expires in 1 hour.
2.  **Run Installer**:
    *   **Windows**:
        ```powershell
        iex (irm https://<server>:8001/api/installer) -Role Puppet -Token "<your-token>"
        ```
    *   **Docker**:
        Use the `node-compose` file generated in the Admin UI.

---

## 4. Network Mounts (Host-Passthrough)
MoP allows Puppets to map network drives (SMB/CIFS) securely using the Host's credentials, without storing passwords in Puppeteer.

1.  **Configure**: Go to **Admin** -> **Network Mounts**.
2.  **Add Mount**:
    *   **Source**: `\\server\share`
    *   **Mount Point**: `/mnt/share` (inside the container)
    *   **Tag**: `windows-nodes` (Target specific groups)
3.  **Deploy**: The configuration is pushed to Puppets primarily via Heartbeat.

---

## 5. Troubleshooting
*   **Puppet Offline**: Check if the `puppets-node` container is running (`docker ps`). Check logs: `docker logs puppets-node-1`.
*   **Certificate Errors**: Ensure the Root CA is trusted or ignore self-signed warnings during initial setup.
*   **Job Failed**: Check the **Standard Error** output in the Job History.

---

## 6. Job Staging & Lifecycle
MoP uses a staging workflow to ensure that jobs pushed from the terminal are reviewed and correctly scheduled before they are executed by nodes.

### Job Statuses
- **DRAFT**: Initial state for jobs pushed via `mop-push job push`. These are not executed by the scheduler.
- **ACTIVE**: Fully-scheduled jobs that are eligible for execution.
- **DEPRECATED**: Old versions of jobs that are no longer executed but kept for history.
- **REVOKED**: Jobs that have been disabled by an administrator.

### The Staging Workflow
1. **Push from CLI**: Use `mop-push job push --name my-job --script script.py --key operator.key` to upload a job script. It enters the **DRAFT** state.
2. **Review in Dashboard**: Navigate to the **Scheduled Jobs** page and click the **STAGING** tab.
3. **Inspect & Finalize**: Click the expansion arrow to view the script content. Use the **Edit** action to set the cron schedule and target tags.
4. **Publish**: Click the **Send/Publish** button. The job status transitions to **ACTIVE** and it moves to the main list.

### Governance
- Only **Admins** can set a job to `REVOKED`.
- A job must be in `ACTIVE` status to be dispatched to nodes.
- `DRAFT` jobs require both a valid User Session (JWT) and a valid local Ed25519 signature to be accepted by the control plane.
