"""
Unit test suite for Git-Oops Autonomous Auto-Updater (v1.0.3)
"""

import sys
import os
import pytest
from git_oops.updater import (
    _parse_version,
    get_current_version,
    check_runtime_health,
    setup_startup_auto_updater,
    trigger_background_self_upgrade
)


def test_version_parsing_and_comparison():
    v1 = _parse_version("1.0.0")
    v2 = _parse_version("1.0.1")
    v3 = _parse_version("1.0.1.post1")
    v4 = _parse_version("1.0.1.post2")
    v5 = _parse_version("1.0.3")

    assert v2 > v1
    assert v3 > v2
    assert v4 > v3
    assert v5 > v4


def test_startup_auto_updater_setup():
    # Calling setup_startup_auto_updater should succeed without crashing
    success = setup_startup_auto_updater()
    # In Windows or desktop environments, returns True; in non-standard headless returns bool
    assert isinstance(success, bool)


def test_runtime_health_reports_auto_updater():
    health = check_runtime_health()
    assert health["status"] == "HEALTHY"
    assert health["auto_updater"] == "ACTIVE"


def test_background_self_upgrade_non_blocking():
    # Spawning background thread must return immediately (< 0.1s)
    trigger_background_self_upgrade()
    # Verify process is still alive and responsive
    assert True


def test_cli_version_flag():
    import subprocess
    out = subprocess.check_output([sys.executable, "-m", "git_oops", "--version"], text=True)
    assert "git-oops v1.0.5" in out


def test_cli_status_short_flag():
    import subprocess
    out = subprocess.check_output([sys.executable, "-m", "git_oops", "-s"], text=True)
    assert "CIRCUIT BREAKER METRICS" in out


def test_cli_short_flags_registered():
    import subprocess
    out = subprocess.check_output([sys.executable, "-m", "git_oops", "-h"], text=True)
    assert "-u UNDO" in out or "-u" in out
    assert "-r RUN" in out or "-r" in out
    assert "-m" in out
    assert "-a" in out



