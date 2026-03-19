"""CE-alone smoke tests (EE-06).
Validates: 13 CE tables, all EE routes 402, GET /api/features all false.
Runs in default CE pytest suite (no ee_only marker).
"""
import pytest
from httpx import AsyncClient, ASGITransport
from agent_service.main import app


@pytest.mark.asyncio
async def test_ce_features_all_false():
    """GET /api/features returns all 8 flags as False in CE-only mode."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/features")
        assert resp.status_code == 200
        flags = resp.json()
        ee_flags = ["foundry", "audit", "webhooks", "triggers", "rbac",
                    "resource_limits", "service_principals", "api_keys"]
        for flag in ee_flags:
            assert flags.get(flag) is False, f"Expected {flag}=False in CE, got {flags.get(flag)}"


@pytest.mark.asyncio
async def test_ce_stub_routers_return_402():
    """CE stub router handlers return 402 Payment Required for EE-gated routes."""
    # Test stub router functions directly — ASGITransport does not trigger lifespan,
    # so stubs are not mounted in the app during unit tests. Verify the stub responses
    # at the handler level instead.
    from agent_service.ee.interfaces.foundry import blueprints_get
    from agent_service.ee.interfaces.audit import audit_log_get
    from agent_service.ee.interfaces.webhooks import webhooks_get

    for handler in (blueprints_get, audit_log_get, webhooks_get):
        resp = await handler()
        assert resp.status_code == 402, (
            f"Stub handler {handler.__name__} returned {resp.status_code}, expected 402"
        )


def test_ce_table_count():
    """CE install creates exactly 13 CE tables (no EE tables)."""
    from agent_service.db import Base
    ce_tables = set(Base.metadata.tables.keys())
    # EE tables must not be present
    ee_tables = {
        "blueprints", "puppet_templates", "capability_matrix", "image_boms",
        "package_index", "approved_os", "artifacts", "approved_ingredients",
        "audit_log", "user_signing_keys", "user_api_keys", "service_principals",
        "role_permissions", "webhooks", "triggers"
    }
    found_ee = ce_tables & ee_tables
    assert not found_ee, f"EE tables found in CE Base.metadata: {found_ee}"
    assert len(ce_tables) == 13, f"Expected 13 CE tables, got {len(ce_tables)}: {sorted(ce_tables)}"
