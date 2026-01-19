# 3rd Party Tool Audit Report

This document lists all third-party tools, libraries, and frameworks used in the **Master of Puppets** project. It is intended for the Datasec team security audit.

## Infrastructure & Runtime

### Podman
*   **Usage**: Container runtime for executing specific nodes and the server stack. Used to isolate the "Node" processes and the Server components (Agent, Model, DB).
*   **Source**: Open Source (Apache 2.0).
*   **Rationale**: Chosen over Docker Desktop for Windows compatibility without licensing costs (for enterprise) and its daemonless architecture which improves security boundaries. It also integrates well with Systemd/User services (though currently using `podman-compose`).

### Docker / Podman Compose
*   **Usage**: Orchestration of multi-container applications (Server stack: DB + Backend + Dashboard).
*   **Source**: Open Source (Apache 2.0).
*   **Rationale**: Standard tool for defining and running multi-container applications. `podman-compose` was specifically chosen to bridge the gap between Docker Compose syntax and the Podman backend on Windows.

### PostgreSQL (Official Alpine Image)
*   **Usage**: Primary relational database for the Agent Service (Jobs, Heartbeats, etc.).
*   **Source**: Open Source (PostgreSQL License).
*   **Rationale**: Industry standard for reliable relational data storage. The Alpine variant was chosen for minimal footprint (~200MB vs ~1GB).

### Python (3.12-slim)
*   **Usage**: Core runtime for the Agent Service, Environment Service (Node), and Maintenance Scripts.
*   **Source**: Open Source (PSF).
*   **Rationale**: The primary language for AI/ML workloads. Version 3.12 selected for latest performance improvements. `slim` image chosen to reduce attack surface (fewer installed system binaries).

### Step CLI (`step`)
*   **Usage**: Used inside the Server container to issue and manage mutual TLS (mTLS) certificates and tokens.
*   **Source**: Open Source (Apache 2.0).
*   **Rationale**: Simplifies PKI (Public Key Infrastructure). Chosen to avoid implementing complex CA logic manually in Python.

### curl
*   **Usage**: Used in Installer scripts (`install_node.ps1`) to download configurations and boostrap the node.
*   **Source**: Open Source (MIT/curl).
*   **Rationale**: Ubiquitous tool for data transfer. Bundled with Windows 10/11 by default now.

---

## Backend Frameworks & Libraries (Python)

### FastAPI (`fastapi`)
*   **Usage**: Web framework for the Agent Service API.
*   **Source**: Open Source (MIT).
*   **Rationale**: Modern, high-performance web framework. Chosen for its automatic OpenAPI documentation (Swagger UI), native async support (crucial for concurrency), and strong typing integration with Pydantic.

### Uvicorn (`uvicorn`)
*   **Usage**: ASGI Web Server implementation to run FastAPI.
*   **Source**: Open Source (BSD).
*   **Rationale**: Standard production-grade ASGI server for FastAPI.

### Pydantic (`pydantic`)
*   **Usage**: Data validation and settings management.
*   **Source**: Open Source (MIT).
*   **Rationale**: Enforces type safety at runtime, ensuring API inputs and database models are valid.

### SQLAlchemy (`sqlalchemy`) + AsyncPG (`asyncpg`)
*   **Usage**: ORM (Object Relational Mapper) and Database Driver.
*   **Source**: Open Source (MIT).
*   **Rationale**: `SQLAlchemy` is the standard Python ORM. `AsyncPG` is the fastest PostgreSQL driver for Python, chosen to prevent database I/O from blocking the async event loop.

### Cryptography (`cryptography`) / Python-Jose (`python-jose`)
*   **Usage**: Handling encryption, private keys, and JWT (JSON Web Tokens) encoding/decoding.
*   **Source**: Open Source (Apache 2.0 / MIT).
*   **Rationale**: De-facto standards for cryptographic primitives in Python. `python-jose` specifically handles the JWT OIDC-style tokens used for Node authentication.

### APScheduler (`apscheduler`)
*   **Usage**: In-process task scheduling (Heartbeat monitoring, Job timeout checks).
*   **Source**: Open Source (MIT).
*   **Rationale**: Lightweight alternative to running a full Celery + Redis stack for simple background tasks. Reduces infrastructure complexity.

### Passlib (`passlib`) + Bcrypt (`bcrypt`)
*   **Usage**: Password hashing for database users.
*   **Source**: Open Source (BSD).
*   **Rationale**: Standard secure password hashing libraries.

---

## Frontend Tools (Node.js / React)

### Vite (`vite`)
*   **Usage**: Build tool and development server for the Dashboard.
*   **Source**: Open Source (MIT).
*   **Rationale**: Extremely fast build times compared to Webpack. Modern standard for React development.

### React (`react`) + React DOM (`react-dom`)
*   **Usage**: User Interface library.
*   **Source**: Open Source (MIT).
*   **Rationale**: The most widely usage frontend library, ensuring component reusability and developer familiarity.

### React Router (`react-router-dom`)
*   **Usage**: Client-side routing (handling URL navigation without page reloads).
*   **Source**: Open Source (MIT).
*   **Rationale**: Standard routing library for React.

### Recharts (`recharts`)
*   **Usage**: Graphing and charting library. Used to visualize job failure trends on the dashboard.
*   **Source**: Open Source (MIT).
*   **Rationale**: Composable charting library built on React components.

### JWT Decode (`jwt-decode`)
*   **Usage**: Client-side parsing of JWTs to display user info or expiration.
*   **Source**: Open Source (MIT).
*   **Rationale**: Lightweight utility to read tokens without verifying them (verification happens on server).

### ESLint (`eslint`)
*   **Usage**: Static code analysis (Linting).
*   **Source**: Open Source (MIT).
*   **Rationale**: Ensures code quality and consistency across the frontend codebase.
