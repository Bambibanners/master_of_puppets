"""
TDD stub for Phase 29 direct mode startup guard requirement.
The 'direct' execution mode bypass must be removed; nodes should raise
a clear error at startup if the configured runtime is unavailable.
"""
import pytest


def test_direct_mode_raises_on_startup():
    """direct EXECUTION_MODE must raise RuntimeError at startup if no container runtime found.
    Previously 'direct' mode silently bypassed runtime detection — this must be removed.
    Implement after runtime.py changes in plan 03."""
    assert False, "implement after runtime.py changes in plan 03"
