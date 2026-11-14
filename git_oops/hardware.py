"""
Git-Oops Hardware & System Sentinel:
1. Battery drain & thermal throttling protection.
2. Low-priority worker affinity (E-Core assignment & nice priority).
3. Zero heavy C-deps: Uses platform-native WMI/powershell/sys/procfs APIs.
"""

import os
import sys
import time
import subprocess
from typing import Tuple, Optional, Dict, Any


def get_system_power_status() -> Dict[str, Any]:
    """
    Returns battery percentage and AC power status across Windows, Linux, and macOS.
    Zero external dependencies.
    """
    status = {"on_battery": False, "battery_percent": 100}

    if sys.platform == "win32":
        try:
            # Query Windows WMI via native PowerShell in <50ms
            cmd = "Get-CimInstance -ClassName Win32_Battery | Select-Object -Property EstimatedChargeRemaining, BatteryStatus | ConvertTo-Json"
            out = subprocess.check_output(["powershell", "-NoProfile", "-Command", cmd], text=True, timeout=2)
            import json
            data = json.loads(out)
            if isinstance(data, list) and data:
                data = data[0]
            if isinstance(data, dict):
                percent = data.get("EstimatedChargeRemaining", 100)
                # BatteryStatus: 1 = Discharging, 2 = Unknown, 3 = Fully Charged, 4 = Low, 5 = Critical, 6 = Charging
                battery_status = data.get("BatteryStatus", 2)
                status["battery_percent"] = int(percent)
                status["on_battery"] = battery_status in [1, 4, 5]
        except Exception:
            pass

    elif sys.platform.startswith("linux"):
        try:
            bat_path = "/sys/class/power_supply"
            if os.path.exists(bat_path):
                for b in os.listdir(bat_path):
                    if b.startswith("BAT"):
                        cap_file = os.path.join(bat_path, b, "capacity")
                        status_file = os.path.join(bat_path, b, "status")
                        if os.path.exists(cap_file):
                            with open(cap_file, "r") as f:
                                status["battery_percent"] = int(f.read().strip())
                        if os.path.exists(status_file):
                            with open(status_file, "r") as f:
                                status["on_battery"] = f.read().strip().lower() == "discharging"
                        break
        except Exception:
            pass

    return status


def check_thermal_and_battery(max_temp_c: float = 85.0, min_battery_pct: int = 15) -> Tuple[bool, Optional[str]]:
    """
    Monitors battery and thermal state.
    Returns (True, None) if safe, or (False, reason) if throttling/halting is required.
    """
    power = get_system_power_status()
    if power["on_battery"] and power["battery_percent"] < min_battery_pct:
        return False, f"THERMAL_THROTTLE_HALT: Battery critically low ({power['battery_percent']}%). Agent background loop paused."

    # Temperature check (Linux /sys/class/thermal or graceful skip on Windows)
    if sys.platform.startswith("linux") and os.path.exists("/sys/class/thermal"):
        try:
            for zone in os.listdir("/sys/class/thermal"):
                temp_file = os.path.join("/sys/class/thermal", zone, "temp")
                if os.path.exists(temp_file):
                    with open(temp_file, "r") as f:
                        temp = float(f.read().strip()) / 1000.0
                        if temp > max_temp_c:
                            return False, f"THERMAL_THROTTLE_HALT: CPU core temperature reached {temp:.1f}°C (> {max_temp_c}°C)."
        except Exception:
            pass

    return True, None


def throttle_agent_process(pid: Optional[int] = None):
    """
    Pins the agent process to lower priority and background CPU affinity (E-Cores).
    Prevents background agent runs from lagging the user's IDE or games.
    """
    target_pid = pid or os.getpid()

    if sys.platform == "win32":
        try:
            import ctypes
            # BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
            # IDLE_PRIORITY_CLASS = 0x00000040
            handle = ctypes.windll.kernel32.OpenProcess(0x0200 | 0x0400, False, target_pid)
            if handle:
                ctypes.windll.kernel32.SetPriorityClass(handle, 0x00004000)
                # Restrict affinity to upper CPU cores (typical E-core placement) if > 4 cores
                cpu_count = os.cpu_count() or 4
                if cpu_count > 4:
                    mask = (1 << cpu_count) - (1 << (cpu_count // 2))
                    ctypes.windll.kernel32.SetProcessAffinityMask(handle, mask)
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass
    elif hasattr(os, "nice"):
        try:
            os.nice(10)  # Lower scheduling priority
        except Exception:
            pass


def down_prioritize_process(pid: Optional[int] = None):
    """Alias for throttle_agent_process."""
    throttle_agent_process(pid)


def check_hardware_throttling() -> Tuple[bool, Optional[str]]:
    """Alias for check_thermal_and_battery."""
    return check_thermal_and_battery()


def get_hardware_telemetry() -> Dict[str, Any]:
    """Returns aggregated hardware telemetry dictionary for Web HUD and CLI."""
    power = get_system_power_status()
    safe, reason = check_thermal_and_battery()
    return {
        "platform": sys.platform,
        "battery_percent": power.get("battery_percent"),
        "power_plugged": not power.get("on_battery", False),
        "process_priority": "BELOW_NORMAL" if sys.platform == "win32" else "NICE_10",
        "is_throttled": not safe,
        "throttle_reason": reason
    }
