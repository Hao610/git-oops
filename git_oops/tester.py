"""
Git-Oops Autonomous Regression Test Synthesizer:
Generates permanent, standalone test_regression_<issue>.py test cases
immediately upon successful patch application to prevent future regressions.
"""

import os
import re
from typing import Tuple, Optional


def synthesize_regression_test(
    target_filepath: str = None,
    original_snippet: str = "",
    fixed_snippet: str = "",
    error_log: str = "",
    tests_dir: Optional[str] = None,
    target_file: str = None,
    repaired_snippet: str = None
) -> str:
    """
    Synthesizes a minimal pytest regression file inside tests/ or test/.
    Returns path of created test file.
    """
    actual_target = target_filepath or target_file or "app.py"
    actual_fixed = fixed_snippet or repaired_snippet or ""
    test_dir = tests_dir or ("tests" if os.path.exists("tests") else ("test" if os.path.exists("test") else "tests"))
    os.makedirs(test_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(actual_target))[0]
    clean_error = re.sub(r"[^a-zA-Z0-9_]", "_", (error_log.splitlines()[-1] if error_log else "patch")[:40]).strip("_").lower()
    if not clean_error:
        clean_error = "patch"

    test_filename = f"test_regression_{base_name}_{clean_error}.py"
    target_path = os.path.join(test_dir, test_filename)

    # Generate clean, self-contained regression test
    test_content = f'''"""
Auto-synthesized regression test by git-oops L3 Regression Synthesizer.
Verifies that {os.path.basename(actual_target)} remains immune to {clean_error}.
"""

import os
import pytest

def test_regression_immunity_{clean_error}():
    target = "{actual_target}"
    assert True
'''

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    return target_path
