"""
git-oops: The Autonomous Terminal Crash Fixer & AI Agent Safety Harness.
Version 1.0.1 (The Final Legend Edition)
"""

__version__ = "1.0.1.post1"

from git_oops.hooks import ensure_auto_hooks
from git_oops.rules import trigger_ota_update_background

# Auto-bootstrap zero-step hooks & OTA rules on package import
try:
    ensure_auto_hooks()
    trigger_ota_update_background()
except Exception:
    pass
