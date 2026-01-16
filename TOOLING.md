# Tooling & Architecture Decisions

## Core Architecture: Three-Service Pull-Model
**Rationale**: Decoupling the logic (Model) from the coordination (Agent) and the execution (Environment) allows for independent scaling and failure isolation.
- **Model Service**: Pure logic. Can be versioned independently.
- **Agent Service**: The stable coordinator. Manages state and resource constraints.
- **Environment Service**: The volatile worker. Can be restarted or replaced without affecting the core state.

## Database: SQLite (Initial Dev) -> PostgreSQL (Production)
**Rationale**: 
- **SQLite**: Zero-configuration, file-based, perfect for portable development and rapid prototyping.
- **PostgreSQL**: Chosen for production due to robust JSONB support (future migration), row-level locking, and proven reliability for transactional state management.
- **Decision**: Develop against a SQL interface (SQLAlchemy/Raw SQL) that is compatible with both, using text-based JSON storage in SQLite to mimic Postgres JSONB.

## Backend Framework: FastAPI
**Rationale**: 
- High performance (Asynchronous).
- Automatic OpenAPI documentation (essential for the Dashboard and Client generation).
- Type safety with Pydantic.

## Communication: HTTP/2 (HTTPS)
**Rationale**: 
- **Zero-Trust**: Every node must authenticate.
- **Standard**: Easy to debug, widely supported, firewall-friendly.
- **Pull-Model**: Nodes initiate connections, avoiding complexities of NAT traversal for the Agent.

## Dependencies
### Python 3.12+
- `fastapi`: Web framework.
- `uvicorn`: ASGI server.
- `httpx`: Async HTTP client for the Nodes.
- `pydantic`: Data validation and settings management.
- `sqlite3`: Standard library, no extra install needed (for now).

## Development Tooling
- **Git**: Version control. "Little and often" strategy.
- **Progress Handover**: `PROGRESS_HANDOVER.md` ensures agentic continuity.
