"""
Git-Oops Obsidian Glassmorphism Web HUD Server
Pure Python zero-dependency web dashboard for live AI agent safety monitoring,
circuit breaker metrics, crash replay timelines, and instant panic rollback.
"""

import os
import sys
import json
import time
import socket
import threading
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

from git_oops.circuit_breaker import get_daily_spend, get_default_config
from git_oops.hardware import check_hardware_throttling, get_hardware_telemetry
from git_oops.blackbox import list_flight_events
from git_oops.watchdog import acquire_agent_lock, release_agent_lock
from git_oops.salvage import run_reflog_autopsy
from git_oops.hooks import run_l3_preflight

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GIT-OOPS // HUD</title>
    <style>
        :root {
            --bg-void: #050507;
            --surface-glass: rgba(18, 18, 24, 0.75);
            --surface-glass-hover: rgba(26, 26, 36, 0.85);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(0, 255, 200, 0.3);
            --accent-cyan: #00ffc8;
            --accent-crimson: #ff0055;
            --accent-amber: #ffb700;
            --accent-purple: #a855f7;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "JetBrains Mono", monospace;
        }

        body {
            background: var(--bg-void);
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px;
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(0, 255, 200, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(168, 85, 247, 0.05) 0%, transparent 40%);
            background-attachment: fixed;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 28px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-icon {
            font-size: 28px;
            text-shadow: 0 0 12px var(--accent-cyan);
        }

        .brand h1 {
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 2px;
            background: linear-gradient(135deg, #ffffff, var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 255, 200, 0.1);
            border: 1px solid var(--accent-cyan);
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1px;
            color: var(--accent-cyan);
            box-shadow: 0 0 16px rgba(0, 255, 200, 0.2);
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-cyan);
            border-radius: 50%;
            animation: pulse 1.8s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.7; }
            50% { transform: scale(1.4); opacity: 1; box-shadow: 0 0 8px var(--accent-cyan); }
            100% { transform: scale(0.9); opacity: 0.7; }
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 28px;
        }

        .card {
            background: var(--surface-glass);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.25s ease;
            position: relative;
            overflow: hidden;
        }

        .card:hover {
            border-color: var(--border-glow);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
        }

        .card-title {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
        }

        .metric-value {
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
        }

        .progress-bar-bg {
            background: rgba(255, 255, 255, 0.06);
            height: 6px;
            border-radius: 999px;
            overflow: hidden;
            margin-top: 10px;
        }

        .progress-bar-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
            width: 0%;
            transition: width 0.5s ease;
        }

        .card-detail {
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 8px;
            line-height: 1.5;
        }

        .table-card {
            grid-column: 1 / -1;
        }

        .event-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 12px;
        }

        .event-table th, .event-table td {
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border-subtle);
        }

        .event-table th {
            color: var(--text-muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-subtle);
            color: var(--text-main);
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.2);
        }

        .btn-danger {
            background: rgba(255, 0, 85, 0.15);
            border-color: var(--accent-crimson);
            color: var(--accent-crimson);
        }

        .btn-danger:hover {
            background: var(--accent-crimson);
            color: #fff;
            box-shadow: 0 0 15px rgba(255, 0, 85, 0.5);
        }

        .action-bar {
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }

        .code-block {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            padding: 12px;
            font-family: monospace;
            font-size: 12px;
            color: var(--accent-cyan);
            max-height: 180px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="brand">
            <span class="brand-icon">⚡</span>
            <div>
                <h1>GIT-OOPS // HUD</h1>
                <span style="font-size: 11px; color: var(--text-muted); letter-spacing: 1px;">THE FINAL LEGEND EDITION v1.0.0</span>
            </div>
        </div>
        <div class="status-badge">
            <div class="pulse-dot"></div>
            <span>AUTONOMOUS HARNESS ACTIVE</span>
        </div>
    </div>

    <div class="grid">
        <!-- Daily Spend Circuit Breaker -->
        <div class="card">
            <div class="card-title">
                <span>Daily Spend Circuit Breaker</span>
                <span id="spend-pct" style="color: var(--accent-cyan);">0%</span>
            </div>
            <div class="metric-value" id="spend-val" style="color: var(--accent-cyan);">$0.0000</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="spend-bar"></div>
            </div>
            <div class="card-detail" id="spend-detail">Daily Ceiling: $1.00 USD</div>
        </div>

        <!-- Hardware & CPU Throttle -->
        <div class="card">
            <div class="card-title">
                <span>Hardware & Thermal Throttle</span>
                <span id="hw-status" style="color: var(--accent-cyan);">OPTIMAL</span>
            </div>
            <div class="metric-value" id="cpu-prio" style="font-size: 24px;">BELOW_NORMAL</div>
            <div class="card-detail" id="hw-detail">Battery: Nominal • Temperature: Safe • OS Priority: Throttled</div>
        </div>

        <!-- L3 Pre-Flight Safety Status -->
        <div class="card">
            <div class="card-title">
                <span>L3 Local CI/CD Pre-Flight</span>
                <span style="color: var(--accent-cyan);">READY</span>
            </div>
            <div class="metric-value" style="font-size: 24px; color: var(--accent-cyan);">ZERO-STEP HOOKS</div>
            <div class="card-detail">Machine-wide core.hooksPath active. Sub-second AST taint inspection on commit/push.</div>
        </div>
    </div>

    <div class="grid">
        <!-- Crash Replay Time Machine -->
        <div class="card table-card">
            <div class="card-title">
                <span>Blackbox Flight Events & Crash Timeline</span>
                <button class="btn btn-danger" onclick="panicRevert()">Emergency Salvage Reflog</button>
            </div>
            <table class="event-table">
                <thead>
                    <tr>
                        <th>Step ID</th>
                        <th>Timestamp</th>
                        <th>Actor</th>
                        <th>Target File</th>
                        <th>Action & Motivation</th>
                    </tr>
                </thead>
                <tbody id="events-tbody">
                    <tr>
                        <td colspan="5" style="text-align: center; color: var(--text-muted);">No crash events recorded. Codebase nominal.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div class="grid">
        <div class="card table-card">
            <div class="card-title">
                <span>Live L3 Security & CodeQL Console</span>
                <button class="btn" onclick="runL3Check()">Run Pre-Flight Now</button>
            </div>
            <div class="code-block" id="l3-log">Waiting for pre-flight check trigger...</div>
        </div>
    </div>

    <script>
        async function refreshData() {
            try {
                const res = await fetch('/api/telemetry');
                const data = await res.json();
                
                // Spend
                document.getElementById('spend-val').innerText = '$' + data.daily_spend.toFixed(4);
                const pct = Math.min(100, (data.daily_spend / data.budget) * 100);
                document.getElementById('spend-pct').innerText = pct.toFixed(1) + '%';
                document.getElementById('spend-bar').style.width = pct + '%';
                document.getElementById('spend-detail').innerText = 'Daily Ceiling: $' + data.budget.toFixed(2) + ' USD';
                
                // Hardware
                document.getElementById('cpu-prio').innerText = data.hw.process_priority;
                document.getElementById('hw-detail').innerText = 'Battery: ' + (data.hw.battery_percent ? data.hw.battery_percent + '%' : 'N/A') + ' • Throttle: ' + (data.hw.is_throttled ? 'ACTIVE' : 'NOMINAL');
                
                // Events
                const tbody = document.getElementById('events-tbody');
                if (data.events && data.events.length > 0) {
                    tbody.innerHTML = data.events.map(e => `
                        <tr>
                            <td>#${e.step_id}</td>
                            <td>${e.timestamp}</td>
                            <td>${e.actor}</td>
                            <td><code>${e.target_file}</code></td>
                            <td>${e.action} - ${e.motivation}</td>
                        </tr>
                    `).join('');
                }
            } catch (err) {
                console.error("Telemetry fetch error:", err);
            }
        }

        async function panicRevert() {
            if (!confirm("Execute emergency reflog salvage to rescue uncommitted/lost work?")) return;
            try {
                const res = await fetch('/api/panic_salvage', { method: 'POST' });
                const r = await res.json();
                alert(r.message || "Salvage executed.");
                refreshData();
            } catch (e) {
                alert("Salvage error: " + e);
            }
        }

        async function runL3Check() {
            document.getElementById('l3-log').innerText = "Running L3 local AST taint and secret scan in <0.2s...";
            try {
                const res = await fetch('/api/l3_check', { method: 'POST' });
                const r = await res.json();
                document.getElementById('l3-log').innerText = r.report;
            } catch (e) {
                document.getElementById('l3-log').innerText = "Error running check: " + e;
            }
        }

        setInterval(refreshData, 2500);
        refreshData();
    </script>
</body>
</html>
"""


class OopsHUDHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP Handler for git-oops HUD."""

    def log_message(self, format, *args):
        # Silence HTTP server access logs in terminal
        pass

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif self.path == "/api/telemetry":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            cfg = get_default_config()
            spend = get_daily_spend()
            hw_telemetry = get_hardware_telemetry()
            events = list_flight_events(limit=10)

            data = {
                "daily_spend": spend,
                "budget": cfg.get("daily_budget", 1.0),
                "hw": hw_telemetry,
                "events": events
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/panic_salvage":
            recovered = run_reflog_autopsy()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            msg = f"Salvage complete. Rescued {len(recovered)} lost commit snapshots from reflog."
            self.wfile.write(json.dumps({"success": True, "message": msg}).encode("utf-8"))
        elif self.path == "/api/l3_check":
            passed, violations, report = run_l3_preflight()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"passed": passed, "report": report}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def start_hud_server(port: int = 8443, open_browser: bool = True):
    """Starts the HUD server on specified port (or auto-finds open port)."""
    server = None
    target_port = port
    for p in range(port, port + 20):
        try:
            server = HTTPServer(("127.0.0.1", p), OopsHUDHandler)
            target_port = p
            break
        except OSError:
            continue

    if not server:
        print(f"Error: Unable to bind HUD server to any port in range {port}-{port+20}.")
        return

    url = f"http://127.0.0.1:{target_port}"
    print(f"\n⚡ Git-Oops Obsidian Web HUD active at: {url}")
    print("Press Ctrl+C to stop the dashboard server.\n")

    if open_browser:
        threading.Thread(target=lambda: (time.sleep(0.5), webbrowser.open(url)), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping HUD server...")
        server.server_close()
