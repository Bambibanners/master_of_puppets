# Master of Puppets - Orchestration Toolkit

> **Status**: Production-Ready / Zero-Trust / Observable
> **Current Version**: 1.2.0 (Strict mTLS & Health Centre)

## Overview
**Master of Puppets** is a secure, scalable, and containerized orchestration framework designed for executing defined automation tasks with strict security and observability. It features a Pull-based architecture, Zero-Trust security (mTLS/JWT/Signatures), a comprehensive React Dashboard, and is fully deployable via Docker/Podman.

## System Architecture

### 1. The Puppeteer (Control Plane)
*   **Directory**: `/puppeteer`
*   **Port**: `8001` (HTTPS, mTLS Required)
*   **Components**: Agent Service, Model Service, Database, Dashboard.
*   **Role**: The brain. Manages Job Queue, Node Registration, Authentication (JWT), PKI (CA), and State.
*   **Security**: Enforces strict mutual TLS. Rejects any connection without a valid client certificate signed by the internal Root CA.

### 2. The Puppet (Execution Node)
*   **Directory**: `/puppets`
*   **Role**: The efficient worker. Proactively heartbeats (stats) and polls for work from the Puppeteer. Executes tasks in isolated subprocesses.
*   **Security**: 
    *   **Self-Bootstrapping**: Bootstraps trust via a secure `JOIN_TOKEN` (embedded Root CA).
    *   **Signature Verification**: Verifies digital signatures (RSA-2048) of all jobs before execution.
    *   **Strict mTLS**: Refuses to connect to an unverified Puppeteer.

### 3. Dashboard Health Centre
*   **Directory**: `/puppeteer/dashboard` (Built into Puppeteer stack)
*   **Port**: `5173` (HTTP)
*   **Tech**: React, Vite, TypeScript, TanStack Query, Recharts, Shadcn/ui.
*   **Role**: Real-time telemetry and control.
    *   **Live Metrics**: CPU/RAM sparklines for every node.
    *   **Status Indicators**: Instant feedback on Node health (Online/Offline/Busy).
    *   **Secure Integration**: Connects directly to the backend API via HTTPS.

## Deployment & Operations

### 1. Puppeteer (Server) Deployment
The control plane is designed to be run as a containerized stack.
*   **Location**: `/puppeteer`
*   **Deployment**: Use `docker compose -f compose.server.yaml up -d` to launch the Agent, Model, and Database services.
*   **Configuration**: Ensure `secrets.env` (see `.env.example`) and necessary certificates are present in `/puppeteer/secrets`.

### 2. Dashboard
The dashboard is a React/Vite application that integrates with the Agent Service.
*   **Location**: `/puppeteer/dashboard`
*   **Build**: `npm run build` from the dashboard directory.
*   **Serve**: Assets are served via Nginx in the Puppeteer stack.

### 3. Puppet (Node) Deployment
Nodes are deployed on target execution environments.
*   **Location**: `/puppets`
*   **Deployment**: Use the provided installers in `/puppets/installer` or run via `docker compose -f node-compose.yaml up -d`.

## Verification & Health

The system provides several endpoints and logs for verification:
*   **Health Check**: Access `https://<puppeteer-ip>:8001/health` (requires mTLS).
*   **Dashboard**: Access the UI on port `5173` (or via Nginx proxy).
*   **Logs**: Monitor container logs for secure handshake and job execution events.

## Security Architecture (Zero-Trust)
1.  **Transport**: All communication is TLS 1.3.
2.  **Identity**: Nodes are identified by Client Certificates (CN=NodeID).
3.  **Execution**: Jobs are signed by the Developer/Admin (Private Key) and verified by the Node (Public Key). The Server is a pass-through and cannot forge jobs.

## Development
- **Development Structure**
- **Puppeteer (Central)**: `puppeteer/`
    - Backend: `puppeteer/agent_service`
    - Dashboard: `puppeteer/dashboard`
- **Puppets (Nodes)**: `puppets/`
    - Installer: `puppets/installer`
- **Agent Context**: `.agent/`

### Local Dev Setup
1.  `pip install -r requirements.txt`
2.  `cd dashboard && npm install`
3.  Create `secrets.env` based on `.env.example`.



