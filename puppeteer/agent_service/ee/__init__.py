"""
EE plugin loader. Discovers axiom.ee entry_points and loads them.
If no EE plugin is installed, all feature flags are False and
stub routers serve 402 responses.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class EEContext:
    """Holds feature flags and references to EE router instances."""
    foundry: bool = False
    audit: bool = False
    webhooks: bool = False
    triggers: bool = False
    rbac: bool = False
    resource_limits: bool = False
    service_principals: bool = False
    api_keys: bool = False

def load_ee_plugins(app: Any, engine: Any) -> EEContext:
    """
    Discover and load EE plugins via pkg_resources entry_points.
    Entry point group: 'axiom.ee'

    If no EE plugin found, registers stub routers that return 402.
    """
    ctx = EEContext()

    try:
        import pkg_resources
        plugins = list(pkg_resources.iter_entry_points("axiom.ee"))
        if plugins:
            for ep in plugins:
                plugin_cls = ep.load()
                plugin = plugin_cls(app, engine)
                plugin.register(ctx)
                logger.info(f"Loaded EE plugin: {ep.name}")
        else:
            logger.info("No EE plugins found — running in CE mode")
    except Exception as e:
        logger.warning(f"EE plugin load failed ({e}), continuing in CE mode")

    return ctx
