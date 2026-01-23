# System Architecture

## Overview
**Master of Puppets** is a distributed orchestration platform designed for secure, containerized task execution. It employs a **Zero-Trust** security model where every component—Puppeteer (Control Plane) and Puppets (Nodes)—must be mutually authenticated.

## Components

### 1. Puppeteer (The Control Plane)
*   **Role**: Central Orchestrator, PKI Authority, and API Gateway.
*   **Tech**: FastAPI, Python 3.12, PostgreSQL.
*   **Key Responsibilities**:
    *   **Job Queue**: Manages the dispatch and tracking of jobs.
    *   **PKI**: Issues tokens (`JOIN_TOKEN`) and signs Client Certificates (CSRs).
    *   **Config**: Stores global configurations like Network Mounts.
*   **Components**:
    *   **Agent Service**: The core API and logic.
    *   **Model Service**: The Scheduler (Recurring Task Engine).
    *   **Dashboard**: The React User Interface.

### 2. Puppet (The Execution Node)
*   **Role**: Isolated execution unit (Worker).
*   **Tech**: Podman Container (Python 3.12-slim).
*   **Key Features**:
    *   **Pull-Based**: Proactively polls Puppeteer for work.
    *   **Stateless**: Ephemeral filesystem; identity is regenerated on startup.
    *   **Self-Bootstrapping**: Uses `JOIN_TOKEN` to trust the Root CA and enroll itself.

## Data Flow
1.  **Enrollment**: Puppet starts -> Decodes Token -> Trusts Root CA -> Generates CSR -> Requests Cert -> Puppeteer Signs Cert -> Puppet Authenticated.
2.  **Job Execution**: Scheduler triggers Job -> Puppeteer queues Job -> Puppet polls -> Puppeteer verifies Puppet Cert -> Puppet pulls Job -> Executes -> Reports Result.
