"""CE+EE combined install smoke test (EE-07).
Requires axiom-ee to be pip-installed. Marked ee_only — excluded from CE default run.
Run with: pytest puppeteer/tests/test_ee_smoke.py -v

Note: Tests call EEPlugin.register() directly rather than via ASGITransport because
httpx.ASGITransport does not trigger ASGI lifespan events — load_ee_plugins() would
never run, leaving all flags False and EE routes unmounted.
"""
import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI
from sqlalchemy import create_engine


pytestmark = pytest.mark.ee_only


def _make_mock_engine():
    sync_engine = create_engine("sqlite:///:memory:")
    mock_engine = MagicMock()
    mock_engine.sync_engine = sync_engine
    return mock_engine


@pytest.mark.asyncio
async def test_ee_features_all_true():
    """EEPlugin.register() sets all 8 feature flags to True."""
    pytest.importorskip("ee.plugin", reason="axiom-ee not installed")
    from ee.plugin import EEPlugin
    from agent_service.ee import EEContext

    mock_app = FastAPI()
    plugin = EEPlugin(mock_app, _make_mock_engine())
    ctx = EEContext()
    await plugin.register(ctx)

    ee_flags = ["foundry", "audit", "webhooks", "triggers", "rbac",
                "resource_limits", "service_principals", "api_keys"]
    for flag in ee_flags:
        assert getattr(ctx, flag) is True, f"Expected {flag}=True in CE+EE, got {getattr(ctx, flag)}"


@pytest.mark.asyncio
async def test_ee_blueprints_route_present():
    """After EEPlugin.register(), a /blueprints route is mounted in the app (not a stub)."""
    pytest.importorskip("ee.plugin", reason="axiom-ee not installed")
    from ee.plugin import EEPlugin
    from agent_service.ee import EEContext

    mock_app = FastAPI()
    plugin = EEPlugin(mock_app, _make_mock_engine())
    ctx = EEContext()
    await plugin.register(ctx)

    routes = [getattr(r, "path", "") for r in mock_app.routes]
    blueprint_routes = [r for r in routes if "blueprint" in r.lower()]
    assert len(blueprint_routes) > 0, (
        f"No blueprint routes found after EEPlugin.register(). Routes: {routes}"
    )
