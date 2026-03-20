"""EEPlugin unit tests (EE-02, EE-03).
Tests register() in isolation using an in-memory SQLite DB — no running server needed.
Runs in default CE suite (no ee_only marker) — axiom-ee must be pip-installed.
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine


@pytest.mark.asyncio
async def test_ee_plugin_register_creates_tables():
    """EEPlugin.register() creates all 15 EE tables in an isolated SQLite DB."""
    pytest.importorskip("ee.plugin", reason="axiom-ee not installed — skip EE plugin tests")
    from ee.plugin import EEPlugin

    # Use a fresh in-memory SQLite engine for isolation
    sync_engine = create_engine("sqlite:///:memory:")
    # Create a mock AsyncEngine whose .sync_engine returns our real sync engine
    mock_async_engine = MagicMock()
    mock_async_engine.sync_engine = sync_engine

    # Create a mock FastAPI app
    mock_app = MagicMock()
    mounted_routers = []
    mock_app.include_router.side_effect = lambda r: mounted_routers.append(r)

    from agent_service.ee import EEContext
    ctx = EEContext()

    plugin = EEPlugin(mock_app, mock_async_engine)
    await plugin.register(ctx)

    # Check all EE tables were created
    from sqlalchemy import inspect
    inspector = inspect(sync_engine)
    created_tables = set(inspector.get_table_names())
    expected = {
        "blueprints", "puppet_templates", "capability_matrix", "image_boms",
        "package_index", "approved_os", "artifacts", "approved_ingredients",
        "audit_log", "user_signing_keys", "user_api_keys", "service_principals",
        "role_permissions", "webhooks", "triggers"
    }
    missing = expected - created_tables
    assert not missing, f"Missing EE tables after register(): {missing}"
    assert len(created_tables) == 15, f"Expected 15 EE tables, got {len(created_tables)}: {sorted(created_tables)}"


@pytest.mark.asyncio
async def test_ee_plugin_register_sets_all_flags():
    """EEPlugin.register() sets all 8 EEContext flags to True."""
    pytest.importorskip("ee.plugin", reason="axiom-ee not installed — skip EE plugin tests")
    from ee.plugin import EEPlugin

    sync_engine = create_engine("sqlite:///:memory:")
    mock_async_engine = MagicMock()
    mock_async_engine.sync_engine = sync_engine
    mock_app = MagicMock()

    from agent_service.ee import EEContext
    ctx = EEContext()

    plugin = EEPlugin(mock_app, mock_async_engine)
    await plugin.register(ctx)

    flags = ["foundry", "audit", "webhooks", "triggers", "rbac",
             "resource_limits", "service_principals", "api_keys"]
    for flag in flags:
        assert getattr(ctx, flag) is True, f"Expected ctx.{flag}=True after register()"
