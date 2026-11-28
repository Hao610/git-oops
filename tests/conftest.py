"""
Global Pytest Configuration and Test Isolation Fixtures for Git-Oops.
Guarantees absolute sandbox isolation so test executions never pollute
the host operator's production memory, audit logs, or circuit breaker telemetry.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def isolate_git_oops_memory(tmp_path, monkeypatch):
    """Isolates blackbox flight recorder, freeze locks, scope, and velocity into an ephemeral temp sandbox."""
    test_mem = str(tmp_path / "sandbox_memory")
    test_home = str(tmp_path / "sandbox_home")
    os.makedirs(test_mem, exist_ok=True)
    os.makedirs(test_home, exist_ok=True)
    monkeypatch.setenv("GIT_OOPS_MEMORY_DIR", test_mem)
    monkeypatch.setenv("GIT_OOPS_HOME", test_home)
    yield test_mem
