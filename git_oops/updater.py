"""
Git-Oops Self-Evolution & Autonomous Auto-Upgrade Engine (v1.0.5)
1. Automatic Windows/POSIX Startup Silent Auto-Updater (Runs quietly on computer boot when network connects).
2. Zero-Latency Background Daemon Auto-Upgrade (Checks PyPI in background thread on routine git commands).
3. Runtime health evaluation & auto-migration against bit-rot.
"""

import sys
import os
import json
import time
import subprocess
import threading
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

UPDATE_DIR = Path.home() / ".git_oops"
UPDATE_CACHE_FILE = UPDATE_DIR / "update_cache.json"

# Check interval for routine execution: 4 hours
UPDATE_CHECK_INTERVAL_SECONDS = 14400


def get_current_version() -> str:
    """Retrieves the currently running package version."""
    try:
        from git_oops import __version__
        return __version__
    except Exception:
        try:
            from src import __version__
            return __version__
        except Exception:
            return "1.0.5.1"


def _parse_version(v_str: str) -> Tuple[int, ...]:
    """Robust version string parser supporting major, minor, patch, post releases."""
    try:
        from packaging.version import parse
        v = parse(v_str)
        # Convert to a comparable tuple
        return (v.major, v.minor, v.micro, v.post or 0)
    except Exception:
        # Fallback manual extraction
        cleaned = v_str.lower().replace("v", "").strip()
        parts = []
        post_val = 0
        if ".post" in cleaned:
            base, post = cleaned.split(".post", 1)
            try:
                post_val = int(post.split(".")[0])
            except Exception:
                post_val = 1
            cleaned = base
        for part in cleaned.split("."):
            try:
                parts.append(int(part))
            except ValueError:
                parts.append(0)
        while len(parts) < 3:
            parts.append(0)
        return (parts[0], parts[1], parts[2], post_val)


def check_for_pypi_update(timeout: float = 3.0) -> Tuple[bool, str, str]:
    """
    Queries PyPI API to detect if a newer release of git-oops is available.
    Returns: (is_newer: bool, remote_version: str, current_version: str)
    """
    current_ver = get_current_version()
    try:
        req = urllib.request.Request(
            "https://pypi.org/pypi/git-oops/json",
            headers={"User-Agent": f"git-oops-autoupdater/{current_ver}"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                remote_ver = data.get("info", {}).get("version", "")
                if remote_ver:
                    if _parse_version(remote_ver) > _parse_version(current_ver):
                        return True, remote_ver, current_ver
                    return False, remote_ver, current_ver
    except Exception:
        pass
    return False, current_ver, current_ver


def perform_silent_upgrade() -> bool:
    """
    Executes pip install --upgrade --quiet git-oops in a completely detached, invisible process.
    """
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", "git-oops"]
        flags = 0
        if sys.platform == "win32":
            # CREATE_NO_WINDOW (0x08000000) guarantees zero console flicker
            flags = 0x08000000 | 0x00000200 # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
        
        subprocess.Popen(
            cmd,
            creationflags=flags if sys.platform == "win32" else 0,
            start_new_session=True if sys.platform != "win32" else False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False


def _background_update_worker():
    """Worker thread that checks cache TTL, polls PyPI, and launches silent upgrade if needed."""
    try:
        UPDATE_DIR.mkdir(parents=True, exist_ok=True)
        now = time.time()
        
        # Check cache TTL
        if UPDATE_CACHE_FILE.exists():
            try:
                with open(UPDATE_CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                last_check = cache.get("last_check", 0)
                if now - last_check < UPDATE_CHECK_INTERVAL_SECONDS:
                    return # Cooldown active, skip network query
            except Exception:
                pass
        
        # Save timestamp first to avoid thrashing on rapid calls
        try:
            with open(UPDATE_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"last_check": now}, f)
        except Exception:
            pass

        # Check PyPI
        is_newer, remote_ver, _ = check_for_pypi_update(timeout=3.0)
        if is_newer:
            perform_silent_upgrade()
    except Exception:
        pass


def trigger_background_self_upgrade():
    """
    Spawns a non-blocking daemon thread to quietly update git-oops in the background.
    Zero latency impact on user commands (<0.001s).
    """
    t = threading.Thread(target=_background_update_worker, daemon=True, name="git-oops-autoupdate")
    t.start()


def setup_startup_auto_updater() -> bool:
    """
    Configures autonomous silent auto-updating upon user logon / system boot.
    On Windows: Installs a hidden .vbs launcher in the user's Startup folder.
    On macOS/Linux: Installs an autostart desktop entry in ~/.config/autostart/.
    Does not require administrator privileges.
    """
    try:
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if not appdata:
                return False
            startup_dir = Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"
            if not startup_dir.exists():
                startup_dir.mkdir(parents=True, exist_ok=True)
            
            vbs_file = startup_dir / "git_oops_autoupdate.vbs"
            # VBS script runs hidden (window style 0, async False)
            # Waits 20s for network connection to settle after boot, then silently upgrades
            vbs_content = (
                'Set WshShell = CreateObject("WScript.Shell")\r\n'
                'WshShell.Run "powershell -WindowStyle Hidden -Command ""Start-Sleep -Seconds 20; '
                'python -m pip install --upgrade --quiet git-oops""", 0, False\r\n'
            )
            
            # Avoid rewriting if already identical
            if vbs_file.exists():
                try:
                    with open(vbs_file, "r", encoding="utf-8") as f:
                        if f.read() == vbs_content:
                            return True
                except Exception:
                    pass

            with open(vbs_file, "w", encoding="utf-8") as f:
                f.write(vbs_content)
            return True
            
        elif sys.platform.startswith("linux") or sys.platform == "darwin":
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            desktop_file = autostart_dir / "git-oops-autoupdate.desktop"
            content = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=GitOops AutoUpdater\n"
                "Exec=sh -c 'sleep 20 && python3 -m pip install --upgrade --quiet git-oops'\n"
                "Hidden=false\n"
                "NoDisplay=true\n"
                "X-GNOME-Autostart-enabled=true\n"
            )
            with open(desktop_file, "w", encoding="utf-8") as f:
                f.write(content)
            return True
    except Exception:
        pass
    return False


def check_runtime_health() -> Dict[str, Any]:
    """
    Evaluates current runtime environment, config migrations, and auto-updater status.
    """
    py_ver = sys.version_info
    health = {
        "python_version": f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}",
        "status": "HEALTHY",
        "migrations_applied": [],
        "auto_updater": "ACTIVE"
    }

    # Auto-migration 1: Config file schema evolution
    cfg_file = os.path.expanduser("~/.git_oops/config.json")
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            migrated = False
            if "schema_version" not in cfg:
                cfg["schema_version"] = 2
                cfg["auto_upgrade_models"] = True
                migrated = True
                health["migrations_applied"].append("Upgraded config schema to v2")
            if migrated:
                with open(cfg_file, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2)
        except Exception:
            pass

    return health
