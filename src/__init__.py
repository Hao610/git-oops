"""
git-oops: The Autonomous Terminal Crash Fixer & AI Agent Safety Harness.
Version 1.0.5.1 (Enterprise Edition)
"""

__version__ = "1.0.5.1"

from src.hooks import ensure_auto_hooks
from src.rules import trigger_ota_update_background
from src.updater import setup_startup_auto_updater, trigger_background_self_upgrade

# Auto-bootstrap zero-step hooks, OTA security rules, and autonomous auto-updater
try:
    ensure_auto_hooks()
    trigger_ota_update_background()
    setup_startup_auto_updater()
    trigger_background_self_upgrade()
except Exception:
    pass
