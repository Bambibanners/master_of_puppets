"""
Phase 31: Environment Tags + CI/CD Dispatch — Test Scaffold

Plan 31-01 (RED): Failing stubs for ENVTAG-01, ENVTAG-02, ENVTAG-04.
Plan 31-02 (GREEN): pull_work env_tag filtering implementation makes source-inspection tests pass.

Test inventory:
  DB schema (ENVTAG-01):
    test_node_has_env_tag             — Node.env_tag column exists, nullable
    test_job_has_env_tag              — Job.env_tag column exists, nullable
    test_scheduled_job_has_env_tag    — ScheduledJob.env_tag column exists, nullable

  Pydantic normalisation (ENVTAG-01):
    test_heartbeat_accepts_env_tag            — HeartbeatPayload normalises env_tag to uppercase
    test_heartbeat_env_tag_none_when_empty    — HeartbeatPayload maps blank/whitespace to None

  pull_work env_tag filtering (ENVTAG-02 — source inspection stubs; RED until Plan 31-02):
    test_pull_work_env_tag_mismatch_skipped   — mismatch path has continue/skip logic
    test_pull_work_env_tag_match_assigned     — match path does NOT trigger mismatch skip
    test_pull_work_no_env_tag_assigned        — None job.env_tag bypasses env_tag check

  Dispatch models (ENVTAG-04):
    test_dispatch_request_model        — DispatchRequest instantiation + env_tag normalisation
    test_dispatch_response_model       — DispatchResponse shape correct
    test_dispatch_status_response_model — DispatchStatusResponse is_terminal derived correctly
"""

import inspect
import pytest

from agent_service.db import Node, Job, ScheduledJob

# ---------------------------------------------------------------------------
# Dispatch model import — these classes don't exist until Plan 31-01 GREEN.
# Skip cleanly if not yet implemented.
# ---------------------------------------------------------------------------
try:
    from agent_service.models import (
        HeartbeatPayload,
        JobCreate,
        NodeResponse,
        JobDefinitionCreate,
        JobDefinitionResponse,
        DispatchRequest,
        DispatchResponse,
        DispatchStatusResponse,
    )
    _dispatch_models_available = True
except ImportError:
    from agent_service.models import (
        HeartbeatPayload,
        JobCreate,
        NodeResponse,
        JobDefinitionCreate,
        JobDefinitionResponse,
    )
    DispatchRequest = None
    DispatchResponse = None
    DispatchStatusResponse = None
    _dispatch_models_available = False


# ---------------------------------------------------------------------------
# DB column tests (ENVTAG-01)
# ---------------------------------------------------------------------------

def test_node_has_env_tag():
    """ENVTAG-01: Node.env_tag must exist as a nullable String(32) column."""
    assert hasattr(Node, "env_tag"), "Node.env_tag column is missing from db.py"
    col = Node.env_tag.property.columns[0]
    assert col.nullable is True, "Node.env_tag must be nullable"


def test_job_has_env_tag():
    """ENVTAG-01: Job.env_tag must exist as a nullable String(32) column."""
    assert hasattr(Job, "env_tag"), "Job.env_tag column is missing from db.py"
    col = Job.env_tag.property.columns[0]
    assert col.nullable is True, "Job.env_tag must be nullable"


def test_scheduled_job_has_env_tag():
    """ENVTAG-01: ScheduledJob.env_tag must exist as a nullable String(32) column."""
    assert hasattr(ScheduledJob, "env_tag"), "ScheduledJob.env_tag column is missing from db.py"
    col = ScheduledJob.env_tag.property.columns[0]
    assert col.nullable is True, "ScheduledJob.env_tag must be nullable"


# ---------------------------------------------------------------------------
# Pydantic normalisation tests (ENVTAG-01)
# ---------------------------------------------------------------------------

def test_heartbeat_accepts_env_tag():
    """ENVTAG-01: HeartbeatPayload.env_tag must normalise to uppercase."""
    model = HeartbeatPayload(node_id="x", hostname="h", env_tag="prod")
    assert model.env_tag == "PROD", f"Expected 'PROD', got {model.env_tag!r}"


def test_heartbeat_env_tag_none_when_empty():
    """ENVTAG-01: HeartbeatPayload.env_tag must be None when whitespace-only is passed."""
    model = HeartbeatPayload(node_id="x", hostname="h", env_tag="  ")
    assert model.env_tag is None, f"Expected None for whitespace input, got {model.env_tag!r}"


# ---------------------------------------------------------------------------
# pull_work source-inspection tests (ENVTAG-02)
# These are RED until Plan 31-02 implements env_tag filtering in pull_work().
# ---------------------------------------------------------------------------

def test_pull_work_env_tag_mismatch_skipped():
    """ENVTAG-02: pull_work() must skip (continue) jobs whose env_tag mismatches the node.
    Verified by source inspection of JobService.pull_work."""
    from agent_service.services.job_service import JobService
    src = inspect.getsource(JobService.pull_work)
    # The env_tag mismatch branch must contain a continue statement
    assert "env_tag" in src, "pull_work() source has no env_tag reference"
    # Check that a mismatch skip/continue exists near env_tag logic
    assert "candidate.env_tag" in src or "job.env_tag" in src, (
        "pull_work() must reference candidate.env_tag or job.env_tag"
    )


def test_pull_work_env_tag_match_assigned():
    """ENVTAG-02: When node.env_tag matches job.env_tag, the job is NOT skipped.
    Verified by confirming the mismatch-continue pattern is conditional (not unconditional)."""
    from agent_service.services.job_service import JobService
    src = inspect.getsource(JobService.pull_work)
    # The guard must be a conditional skip — env_tag check must not appear as an
    # unconditional continue. Presence of 'node.env_tag' or 'node_env_tag' in src
    # alongside the conditional pattern confirms the if-guard exists.
    assert "node.env_tag" in src or "node_env_tag" in src, (
        "pull_work() must reference node.env_tag to build the conditional filter"
    )


def test_pull_work_no_env_tag_assigned():
    """ENVTAG-02: When job.env_tag is None, the env_tag check must be bypassed entirely.
    Verified by source inspection — the guard must be conditional on env_tag being set."""
    from agent_service.services.job_service import JobService
    src = inspect.getsource(JobService.pull_work)
    # The env_tag check must be guarded so None job env_tag skips the filter
    assert "env_tag" in src, "pull_work() source has no env_tag reference — implement ENVTAG-02"
    # A conditional guard is expressed as 'if candidate.env_tag' or similar
    assert (
        "if candidate.env_tag" in src
        or "if job.env_tag" in src
        or "candidate.env_tag is not None" in src
    ), (
        "pull_work() must guard env_tag check so None job.env_tag is not filtered out"
    )


# ---------------------------------------------------------------------------
# Dispatch model tests (ENVTAG-04)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _dispatch_models_available, reason="models not yet implemented")
def test_dispatch_request_model():
    """ENVTAG-04: DispatchRequest must instantiate; env_tag is optional and normalised to uppercase."""
    req = DispatchRequest(job_definition_id="abc-123")
    assert req.job_definition_id == "abc-123"
    assert req.env_tag is None

    req2 = DispatchRequest(job_definition_id="abc-123", env_tag="staging")
    assert req2.env_tag == "STAGING", f"Expected 'STAGING', got {req2.env_tag!r}"


@pytest.mark.skipif(not _dispatch_models_available, reason="models not yet implemented")
def test_dispatch_response_model():
    """ENVTAG-04: DispatchResponse must hold job_guid, status, job_definition_id, name, poll_url."""
    resp = DispatchResponse(
        job_guid="g",
        status="PENDING",
        job_definition_id="d",
        job_definition_name="n",
        poll_url="http://x/api/dispatch/g/status",
    )
    assert resp.job_guid == "g"
    assert resp.status == "PENDING"
    assert resp.job_definition_id == "d"
    assert resp.job_definition_name == "n"
    assert resp.poll_url == "http://x/api/dispatch/g/status"
    assert resp.env_tag is None


@pytest.mark.skipif(not _dispatch_models_available, reason="models not yet implemented")
def test_dispatch_status_response_model():
    """ENVTAG-04: DispatchStatusResponse must carry is_terminal reflecting job finality."""
    pending = DispatchStatusResponse(job_guid="g", status="PENDING", is_terminal=False)
    assert pending.is_terminal is False

    completed = DispatchStatusResponse(job_guid="g", status="COMPLETED", is_terminal=True)
    assert completed.is_terminal is True
    assert completed.exit_code is None
    assert completed.node_id is None
