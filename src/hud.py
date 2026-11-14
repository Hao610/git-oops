"""
Git-Oops Enterprise Obsidian Web HUD Server
Pure Python zero-dependency web dashboard for live AI agent safety monitoring,
circuit breaker metrics, crash replay timelines, and instant panic rollback.
Fortune-500 Production Grade Edition.
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
from git_oops.blackbox import list_flight_events, clear_flight_events
from git_oops.watchdog import acquire_agent_lock, release_agent_lock
from git_oops.salvage import run_reflog_autopsy
from git_oops.hooks import run_l3_preflight

ENTERPRISE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GIT-OOPS // ENTERPRISE SAFETY HARNESS</title>
    <style>
        :root {
            --bg-void: #06070a;
            --surface-glass: rgba(14, 17, 24, 0.78);
            --surface-glass-hover: rgba(22, 27, 38, 0.88);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(0, 240, 255, 0.35);
            --accent-cyan: #00f0ff;
            --accent-purple: #a855f7;
            --accent-crimson: #ff0055;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
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
            padding: 28px 36px;
            background-image: 
                radial-gradient(circle at 12% 10%, rgba(0, 240, 255, 0.06) 0%, transparent 45%),
                radial-gradient(circle at 88% 90%, rgba(168, 85, 247, 0.06) 0%, transparent 45%);
            background-attachment: fixed;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 22px;
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 28px;
        }

        .brand-meta {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-logo {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(168, 85, 247, 0.2));
            border: 1px solid var(--border-glow);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
        }

        .brand-title h1 {
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 1.5px;
            background: linear-gradient(135deg, #ffffff 40%, var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-sub {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid var(--accent-emerald);
            padding: 7px 16px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.2px;
            color: var(--accent-emerald);
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.18);
        }

        .pulse-dot {
            width: 7px;
            height: 7px;
            background: var(--accent-emerald);
            border-radius: 50%;
            animation: pulse-ring 2s infinite ease-in-out;
        }

        @keyframes pulse-ring {
            0% { transform: scale(0.9); opacity: 0.8; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.9); opacity: 0.8; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        .grid-3 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 22px;
            margin-bottom: 28px;
        }

        .card {
            background: var(--surface-glass);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 22px;
            transition: all 0.25s ease;
            position: relative;
        }

        .card:hover {
            border-color: var(--border-glow);
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.6);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
        }

        .card-label {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
        }

        .metric-big {
            font-size: 34px;
            font-weight: 800;
            letter-spacing: -0.5px;
            line-height: 1.2;
        }

        .progress-track {
            background: rgba(255, 255, 255, 0.05);
            height: 6px;
            border-radius: 999px;
            overflow: hidden;
            margin: 14px 0 8px 0;
        }

        .progress-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
            width: 0%;
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .card-foot {
            font-size: 12px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
        }

        .btn {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-subtle);
            color: var(--text-main);
            padding: 7px 15px;
            border-radius: 7px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.14);
            border-color: rgba(255, 255, 255, 0.25);
            transform: translateY(-1px);
        }

        .btn-danger {
            background: rgba(255, 0, 85, 0.12);
            border-color: rgba(255, 0, 85, 0.5);
            color: #ff3377;
        }

        .btn-danger:hover {
            background: var(--accent-crimson);
            color: #fff;
            border-color: var(--accent-crimson);
            box-shadow: 0 0 16px rgba(255, 0, 85, 0.5);
        }

        .btn-primary {
            background: rgba(0, 240, 255, 0.12);
            border-color: rgba(0, 240, 255, 0.5);
            color: var(--accent-cyan);
        }

        .btn-primary:hover {
            background: var(--accent-cyan);
            color: #000;
            border-color: var(--accent-cyan);
            box-shadow: 0 0 16px rgba(0, 240, 255, 0.4);
        }

        .table-wrap {
            overflow-x: auto;
            margin-top: 14px;
        }

        .audit-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12.5px;
        }

        .audit-table th {
            text-align: left;
            padding: 10px 14px;
            font-size: 10.5px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border-subtle);
        }

        .audit-table td {
            padding: 12px 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            vertical-align: middle;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .badge-agent {
            background: rgba(168, 85, 247, 0.15);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.35);
        }

        .badge-human {
            background: rgba(0, 240, 255, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(0, 240, 255, 0.35);
        }

        .badge-ci {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.35);
        }

        .file-pill {
            font-family: "JetBrains Mono", monospace;
            font-size: 12px;
            background: rgba(0, 240, 255, 0.06);
            color: var(--accent-cyan);
            border: 1px solid rgba(0, 240, 255, 0.2);
            padding: 3px 8px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .file-pill:hover {
            background: rgba(0, 240, 255, 0.16);
            border-color: var(--accent-cyan);
        }

        .code-console {
            background: #040406;
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 16px;
            font-family: "JetBrains Mono", monospace;
            font-size: 12px;
            line-height: 1.6;
            color: #a7f3d0;
            max-height: 220px;
            overflow-y: auto;
            white-space: pre-wrap;
            margin-top: 14px;
        }

        /* Obsidian Toast Notification */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 28px;
            background: rgba(18, 22, 32, 0.95);
            backdrop-filter: blur(16px);
            border: 1px solid var(--accent-cyan);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
            color: var(--text-main);
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            z-index: 1000;
        }

        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="brand-meta">
            <div class="brand-logo">⚡</div>
            <div class="brand-title">
                <h1>GIT-OOPS ENTERPRISE // SAFETY HARNESS</h1>
                <div class="brand-sub">DEFENSE PLATFORM // v{{VERSION}} (ACTIVE L3 DEFENSE)</div>
            </div>
        </div>
        <div class="header-actions">
            <button class="btn" onclick="exportAuditLog()">📥 Export Audit JSON</button>
            <div class="status-pill">
                <div class="pulse-dot"></div>
                <span>SOC-2 HARNESS ONLINE</span>
            </div>
        </div>
    </div>

    <!-- Metric Gauges -->
    <div class="grid-3">
        <!-- Daily Spend Circuit Breaker -->
        <div class="card">
            <div class="card-header">
                <span class="card-label">Daily Spend Circuit Breaker</span>
                <span id="spend-pct" style="color: var(--accent-cyan); font-weight: 700; font-size: 13px;">0.0%</span>
            </div>
            <div class="metric-big" id="spend-val" style="color: var(--accent-cyan);">$0.0000</div>
            <div class="progress-track">
                <div class="progress-fill" id="spend-bar"></div>
            </div>
            <div class="card-foot">
                <span>Daily Ceiling: <b id="spend-limit">$1.00 USD</b></span>
                <span id="spend-status" style="color: var(--accent-emerald);">NORMAL</span>
            </div>
        </div>

        <!-- Hardware & Thermal Throttling -->
        <div class="card">
            <div class="card-header">
                <span class="card-label">Host Thermal & Telemetry</span>
                <span id="hw-status" style="color: var(--accent-emerald); font-weight: 700; font-size: 13px;">OPTIMAL</span>
            </div>
            <div class="metric-big" id="cpu-prio" style="font-size: 26px; color: var(--text-main);">BELOW_NORMAL</div>
            <div class="progress-track">
                <div class="progress-fill" id="battery-bar" style="background: var(--accent-emerald); width: 100%;"></div>
            </div>
            <div class="card-foot">
                <span id="battery-txt">Battery: Nominal</span>
                <span>OS Throttling: Active</span>
            </div>
        </div>

        <!-- L3 Security Gate Status -->
        <div class="card">
            <div class="card-header">
                <span class="card-label">L3 Zero-Step Pre-Flight</span>
                <span style="color: var(--accent-cyan); font-weight: 700; font-size: 13px;">ENFORCED</span>
            </div>
            <div class="metric-big" style="font-size: 24px; color: var(--accent-cyan);">MACHINE-WIDE HOOKS</div>
            <div class="progress-track">
                <div class="progress-fill" style="background: linear-gradient(90deg, var(--accent-cyan), var(--accent-emerald)); width: 100%;"></div>
            </div>
            <div class="card-foot">
                <span>AST Taint & Credential Scan</span>
                <span style="color: var(--accent-cyan);">&lt;0.05s Execution</span>
            </div>
        </div>
    </div>

    <!-- Blackbox Flight Recorder Audit Table -->
    <div class="card" style="margin-bottom: 28px;">
        <div class="card-header">
            <div>
                <span class="card-label">Blackbox Flight Events & Crash Audit Trail</span>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 3px;">Immutable ledger of AI agent modifications, crash diagnoses, and reflog snapshots.</div>
            </div>
            <div style="display: flex; gap: 8px;">
                <button class="btn btn-danger" onclick="panicRevert()">🚨 Disaster Recovery Reflog</button>
                <button class="btn" onclick="clearAuditEvents()">🧹 Purge Audit Trail</button>
            </div>
        </div>
        <div class="table-wrap">
            <table class="audit-table">
                <thead>
                    <tr>
                        <th style="width: 110px;">Event ID</th>
                        <th style="width: 170px;">Timestamp</th>
                        <th style="width: 140px;">Operator / Agent</th>
                        <th style="width: 220px;">Target File</th>
                        <th>Action & Intent</th>
                    </tr>
                </thead>
                <tbody id="events-tbody">
                    <tr>
                        <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 32px;">No crash events recorded. Codebase nominal.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Live L3 CodeQL Security Console -->
    <div class="card">
        <div class="card-header">
            <div>
                <span class="card-label">Live L3 AST Security & Credential Gatekeeper</span>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 3px;">Static taint analysis, dangerous sink inspection (exec/eval), and credential entropy gate.</div>
            </div>
            <button class="btn btn-primary" onclick="runL3Check()">⚡ Run Pre-Flight Scan</button>
        </div>
        <div class="code-console" id="l3-log">[SOC-2 / ISO-27001 AUDIT READY] Waiting for trigger... Press 'Run Pre-Flight Scan' to verify codebase integrity.</div>
    </div>

    <!-- Frosted Toast Notification -->
    <div class="toast" id="toast-notify">
        <span id="toast-icon">✓</span>
        <span id="toast-text">Action completed successfully.</span>
    </div>

    <script>
        let cachedEvents = [];

        function showToast(msg, isError = false) {
            const t = document.getElementById('toast-notify');
            document.getElementById('toast-icon').innerText = isError ? '⚠' : '✓';
            document.getElementById('toast-icon').style.color = isError ? 'var(--accent-crimson)' : 'var(--accent-cyan)';
            t.style.borderColor = isError ? 'var(--accent-crimson)' : 'var(--accent-cyan)';
            document.getElementById('toast-text').innerText = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3500);
        }

        async function refreshData() {
            try {
                const res = await fetch('/api/telemetry');
                const data = await res.json();
                cachedEvents = data.events || [];
                
                // Spend
                document.getElementById('spend-val').innerText = '$' + data.daily_spend.toFixed(4);
                const pct = Math.min(100, (data.daily_spend / data.budget) * 100);
                document.getElementById('spend-pct').innerText = pct.toFixed(1) + '%';
                document.getElementById('spend-bar').style.width = pct + '%';
                document.getElementById('spend-limit').innerText = '$' + data.budget.toFixed(2) + ' USD';
                if (pct >= 90) {
                    document.getElementById('spend-status').innerText = 'TRIPPED';
                    document.getElementById('spend-status').style.color = 'var(--accent-crimson)';
                } else {
                    document.getElementById('spend-status').innerText = 'NORMAL';
                    document.getElementById('spend-status').style.color = 'var(--accent-emerald)';
                }
                
                // Hardware
                document.getElementById('cpu-prio').innerText = data.hw.process_priority || 'NORMAL';
                const battPct = data.hw.battery_percent;
                document.getElementById('battery-txt').innerText = 'Battery: ' + (battPct ? battPct + '%' : 'Nominal (AC)');
                if (battPct) {
                    document.getElementById('battery-bar').style.width = battPct + '%';
                }
                document.getElementById('hw-status').innerText = data.hw.is_throttled ? 'THROTTLED' : 'OPTIMAL';
                document.getElementById('hw-status').style.color = data.hw.is_throttled ? 'var(--accent-amber)' : 'var(--accent-emerald)';
                
                // Events Table
                const tbody = document.getElementById('events-tbody');
                if (data.events && data.events.length > 0) {
                    tbody.innerHTML = data.events.map(e => {
                        const actor = (e.agent_id || e.actor || 'human-operator').toLowerCase();
                        let badgeClass = 'badge-agent';
                        let badgeLabel = '🤖 AGENT';
                        if (actor.includes('human') || actor.includes('operator')) {
                            badgeClass = 'badge-human';
                            badgeLabel = '👤 OPERATOR';
                        } else if (actor.includes('ci') || actor.includes('hook')) {
                            badgeClass = 'badge-ci';
                            badgeLabel = '⚡ CI/CD';
                        }

                        const fullPath = e.target_file || '-';
                        const fileName = fullPath.split(/[/\\\\]/).pop() || fullPath;
                        return `
                        <tr>
                            <td style="font-family: monospace; color: var(--accent-cyan); font-weight: 700;">#${String(e.step_id).slice(-8)}</td>
                            <td style="color: var(--text-muted); font-size: 12px;">${e.timestamp}</td>
                            <td><span class="badge ${badgeClass}">${badgeLabel}</span></td>
                            <td><span class="file-pill" title="${fullPath}">📄 ${fileName}</span></td>
                            <td><span style="font-weight: 600; color: #fff;">${e.action}</span> <span style="color: var(--text-muted); font-size: 12px;">- ${e.motivation}</span></td>
                        </tr>
                        `;
                    }).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 32px;">No crash events recorded. Codebase nominal.</td></tr>';
                }
            } catch (err) {
                console.error("Telemetry error:", err);
            }
        }

        async function clearAuditEvents() {
            if (!confirm("Are you sure you want to purge all blackbox flight events?")) return;
            try {
                const res = await fetch('/api/clear_events', { method: 'POST' });
                const r = await res.json();
                showToast("Audit trail purged successfully.");
                refreshData();
            } catch (e) {
                showToast("Failed to purge audit trail: " + e, true);
            }
        }

        async function panicRevert() {
            if (!confirm("Initiate Emergency Reflog Salvage? Git reflog autopsy will scan for detached and lost commit snapshots.")) return;
            try {
                const res = await fetch('/api/panic_salvage', { method: 'POST' });
                const r = await res.json();
                showToast(r.message || "Disaster recovery executed successfully.");
                refreshData();
            } catch (e) {
                showToast("Reflog recovery error: " + e, true);
            }
        }

        async function runL3Check() {
            const consoleBox = document.getElementById('l3-log');
            consoleBox.innerText = "[EXECUTION INITIATED] Running sub-second AST taint analysis & secret entropy pre-flight scan...\\n";
            try {
                const res = await fetch('/api/l3_check', { method: 'POST' });
                const r = await res.json();
                consoleBox.innerText = r.report;
                showToast(r.passed ? "Pre-flight scan passed. Zero vulnerabilities." : "Pre-flight detected policy violations.", !r.passed);
            } catch (e) {
                consoleBox.innerText = "[ERROR] Pre-flight failed to execute: " + e;
                showToast("Scan error: " + e, true);
            }
        }

        function exportAuditLog() {
            const blob = new Blob([JSON.stringify(cachedEvents, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'git_oops_soc2_audit_trail.json';
            a.click();
            URL.revokeObjectURL(url);
            showToast("Exported compliance audit log as JSON.");
        }

        setInterval(refreshData, 2000);
        refreshData();
    </script>
</body>
</html>
"""


class OopsHUDHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP Handler for git-oops HUD."""

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()

            try:
                from git_oops import __version__
            except Exception:
                try:
                    from src import __version__
                except Exception:
                    __version__ = "1.0.5"

            rendered = ENTERPRISE_HTML_TEMPLATE.replace("{{VERSION}}", __version__)
            self.wfile.write(rendered.encode("utf-8"))
        elif self.path == "/api/telemetry":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()

            cfg = get_default_config()
            spend = get_daily_spend()
            hw_telemetry = get_hardware_telemetry()
            events = list_flight_events(limit=25)

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
        elif self.path == "/api/clear_events":
            clear_flight_events()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
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
    print(f"\\n⚡ Git-Oops Enterprise Web HUD active at: {url}")
    print("Press Ctrl+C to stop the dashboard server.\\n")

    if open_browser:
        threading.Thread(target=lambda: (time.sleep(0.5), webbrowser.open(url)), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nStopping HUD server...")
        server.server_close()
