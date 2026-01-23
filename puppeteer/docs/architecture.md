# System Architecture

## Overview
**Master of Puppets** is a distributed orchestration platform designed for secure, containerized task execution. It employs a **Zero-Trust** security model where every component—Server, Agent, and Node—must be mutually authenticated.

## Components

### 1. Agent Service (The Brain)
*   **Role**: Central Orchestrator, PKI Authority, and API Gateway.
*   **Tech**: FastAPI, Python 3.12, PostgreSQL.
*   **Key Responsibilities**:
    *   **Job Queue**: Manages the dispatch and tracking of jobs.
    *   **PKI**: Issues tokens (`JOIN_TOKEN`) and signs Client Certificates (CSRs).
    *   **Config**: Stores global configurations like Network Mounts.

### 2. Model Service (The Scheduler)
*   **Role**: Recurring Task Engine.
*   **Tech**: APScheduler, SQLAlchemy.
*   **Function**: Works alongside the Agent to trigger jobs based on cron schedules.

### 3. Environment Node (The Worker)
*   **Role**: Isolated execution unit.
*   **Tech**: Podman Container (Python 3.12-slim).
*   **Key Features**:
    *   **Pull-Based**: Proactively polls the Agent for work.
    *   **Stateless**: Ephemeral filesystem; identity is regenerated on startup.
    *   **Self-Bootstrapping**: Uses `JOIN_TOKEN` to trust the Root CA and enroll itself.

### 4. Dashboard (The Control Plane)
*   **Role**: User Interface.
*   **Tech**: React, Vite.
*   **Features**: Node Management, Job Monitoring, Documentation.

## Data Flow
1.  **Enrollment**: Node starts -> Decodes Token -> Trusts Root CA -> Generates CSR -> Requests Cert -> Agent Signs Cert -> Node Authentic.
2.  **Job Execution**: Model triggers Job -> Agent queues Job -> Node polls -> Agent verifies Node Cert -> Node pulls Job -> Executes -> Reports Result.
