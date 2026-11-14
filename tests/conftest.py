"""
Global Pytest Configuration and Test Isolation Fixtures for Git-Oops.
Guarantees absolute sandbox isolation so test executions never pollute
the host operator's production memory, audit logs, or circuit breaker telemetry.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def isolate_git_oops_memory(tmp_path, monkeypatch):
    """Isolates blackbox flight recorder and antibodies into an ephemeral temp sandbox."""
    test_mem = str(tmp_path / "sandbox_memory")
    os.makedirs(test_mem, exist_ok=True)
    monkeypatch.setenv("GIT_OOPS_MEMORY_DIR", test_mem)
    yield test_mem
