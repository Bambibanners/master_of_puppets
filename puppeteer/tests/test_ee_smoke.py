"""CE+EE combined install smoke test (EE-07).
Requires axiom-ee to be pip-installed. Marked ee_only — excluded from CE default run.
Run with: pytest puppeteer/tests/test_ee_smoke.py -v
"""
import pytest
from httpx import AsyncClient, ASGITransport


pytestmark = pytest.mark.ee_only


@pytest.mark.asyncio
async def test_ee_features_all_true():
    """GET /api/features returns all 8 flags as True after CE+EE install."""
    pytest.importorskip("ee.plugin", reason="axiom-ee not installed")
    from agent_service.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/features")
        assert resp.status_code == 200
        flags = resp.json()
        ee_flags = ["foundry", "audit", "webhooks", "triggers", "rbac",
                    "resource_limits", "service_principals", "api_keys"]
        for flag in ee_flags:
            assert flags.get(flag) is True, f"Expected {flag}=True in CE+EE, got {flags.get(flag)}"


@pytest.mark.asyncio
async def test_ee_blueprints_route_live():
    """GET /api/blueprints returns 200 (not 402) after CE+EE install."""
    pytest.importorskip("ee.plugin", reason="axiom-ee not installed")
    from agent_service.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/blueprints")
        # 401 is acceptable (auth required but route exists); 402 means stub — fail
        assert resp.status_code != 402, f"Got 402 (stub router still active) — EE plugin not wired"
        assert resp.status_code in (200, 401), f"Unexpected status: {resp.status_code}"
