"""
TDD stubs for Phase 29 retry wiring requirements.
Covers RETRY-01 (attempt_number tracked per execution) and
RETRY-02 (job_run_id stable across retries, started_at in WorkResponse).

Model-field tests: real assertions (fields exist after plan 29-01).
Implementation stubs: assert False with clear "implement after" messages.
"""
import pytest
from unittest.mock import MagicMock


def test_work_response_has_started_at():
    """RETRY-02: WorkResponse must carry started_at so nodes can report accurate timing."""
    from agent_service.models import WorkResponse
    w = WorkResponse(guid="x", task_type="python_script", payload={}, started_at=None)
    assert hasattr(w, "started_at")
    assert w.started_at is None


def test_work_response_started_at_optional_datetime():
    """WorkResponse.started_at must accept a datetime value."""
    from agent_service.models import WorkResponse
    from datetime import datetime
    ts = datetime(2026, 3, 18, 12, 0, 0)
    w = WorkResponse(guid="x", task_type="python_script", payload={}, started_at=ts)
    assert w.started_at == ts


def test_execution_record_has_attempt_number():
    """RETRY-01: ExecutionRecord must have attempt_number column (nullable int)."""
    from agent_service.db import ExecutionRecord
    er = ExecutionRecord(job_guid="test-guid", status="COMPLETED", attempt_number=1)
    assert er.attempt_number == 1
    er2 = ExecutionRecord(job_guid="test-guid-2", status="COMPLETED")
    assert er2.attempt_number is None


def test_execution_record_has_job_run_id():
    """RETRY-02: ExecutionRecord must have job_run_id column (nullable str)."""
    from agent_service.db import ExecutionRecord
    er = ExecutionRecord(job_guid="test-guid", status="COMPLETED", job_run_id="run-uuid-001")
    assert er.job_run_id == "run-uuid-001"
    er2 = ExecutionRecord(job_guid="test-guid-2", status="COMPLETED")
    assert er2.job_run_id is None


def test_job_has_job_run_id():
    """RETRY-02: Job must have job_run_id column (nullable str) to group all attempts."""
    from agent_service.db import Job
    j = Job(guid="job-001", task_type="python_script", payload="{}", job_run_id="run-uuid-001")
    assert j.job_run_id == "run-uuid-001"
    j2 = Job(guid="job-002", task_type="python_script", payload="{}")
    assert j2.job_run_id is None


def test_attempt_number_first_attempt():
    """RETRY-01: First attempt execution record must have attempt_number=1.
    Implement after job_service.py changes in plan 02."""
    assert False, "implement after job_service.py changes in plan 02"


def test_job_run_id_stable_across_retries():
    """RETRY-02: job_run_id must remain the same UUID across all retry attempts.
    Implement after job_service.py changes in plan 02."""
    assert False, "implement after job_service.py changes in plan 02"


def test_job_run_id_set_at_dispatch():
    """RETRY-02: job_run_id must be assigned when a job is first dispatched (pull_work).
    Implement after job_service.py changes in plan 02."""
    assert False, "implement after job_service.py changes in plan 02"
