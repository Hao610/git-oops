"""
Unit tests for git-oops:
1. Circuit breaker spend limit triggers
2. SHA256 caching deduplication
3. Patch file replacement logic
4. Offline diagnostic fallback
"""

import os
import pytest
from src.circuit_breaker import check_circuit_breaker, record_spend, get_daily_spend, hash_content
from src.engine import diagnose_and_patch, apply_patch_to_file, rollback_file


def test_circuit_breaker_blocks_when_exceeded(monkeypatch):
    """Verify circuit breaker raises PermissionError when daily budget limit is breached."""
    # Mock spend to simulate hitting $5.00 spend
    monkeypatch.setattr("src.circuit_breaker.get_daily_spend", lambda: 5.50)
    
    with pytest.raises(PermissionError) as exc:
        check_circuit_breaker(spend_limit_usd=1.00)
    assert "CIRCUIT BREAKER TRIGGERED" in str(exc.value)


def test_sha256_hashing_consistency():
    h1 = hash_content("test code")
    h2 = hash_content("test code")
    h3 = hash_content("different code")
    assert h1 == h2
    assert h1 != h3


def test_patch_application(tmp_path):
    """Verify string replacement applies safely and cleanly to files."""
    dummy_file = tmp_path / "broken.py"
    dummy_file.write_text("def run():\n    user_id = payload['user_id']\n    return user_id\n", encoding="utf-8")

    orig = "user_id = payload['user_id']"
    fix = "user_id = payload.get('user_id')"

    applied = apply_patch_to_file(str(dummy_file), orig, fix)
    assert applied is True

    updated_content = dummy_file.read_text(encoding="utf-8")
    assert "payload.get('user_id')" in updated_content
    assert "payload['user_id']" not in updated_content


def test_offline_critic_returns_valid_roast_and_diff():
    """Verify offline engine returns schema with roast and patch."""
    res = diagnose_and_patch(
        error_log="KeyError: 'user_id'",
        file_context="user_id = payload['user_id']",
        target_filepath="app.py",
        api_key=""
    )
    assert "roast" in res
    assert "git_patch" in res
    assert "--- a/app.py" in res["git_patch"]


def test_personalities_roast_properly():
    """Verify all caustic personalities return distinct biting roasts."""
    p_kernel = diagnose_and_patch("KeyError", "code", "app.py", personality="kernel", api_key="")
    assert "memory" in p_kernel["roast"].lower() or "mind" in p_kernel["roast"].lower()

    p_chef = diagnose_and_patch("KeyError", "code", "app.py", personality="chef", api_key="")
    assert "RAW" in p_chef["roast"] or "SANDWICH" in p_chef["roast"]

    p_passive = diagnose_and_patch("KeyError", "code", "app.py", personality="passive_aggressive", api_key="")
    assert "previous" in p_passive["roast"].lower() or "😊" in p_passive["roast"]


def test_patch_rollback(tmp_path):
    """Verify applying a patch creates a backup and rollback restores exact original state."""
    dummy_file = tmp_path / "rollback_test.py"
    initial_content = "def test():\n    return 42\n"
    dummy_file.write_text(initial_content, encoding="utf-8")

    orig = "return 42"
    fix = "return 100"

    apply_patch_to_file(str(dummy_file), orig, fix)
    assert "return 100" in dummy_file.read_text(encoding="utf-8")

    # Now rollback
    success = rollback_file(str(dummy_file))
    assert success is True
    assert dummy_file.read_text(encoding="utf-8") == initial_content
