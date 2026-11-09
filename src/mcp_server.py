"""
Git-Oops Native Model Context Protocol (MCP) Server
Allows Claude Desktop, Cursor, Windsurf, and Antigravity to attach to git-oops.
Speaks standard JSON-RPC 2.0 over stdio without any external networking baggage.
"""

import sys
import json
from src.firewall import check_command_safety
from src.squeezer import compress_traceback, redact_secrets
from src.guardian import check_ghost_imports
from src.engine import diagnose_and_patch, apply_patch_to_file

MCP_TOOLS = [
    {
        "name": "git_oops_diagnose",
        "description": "Analyzes a terminal crash traceback, roasts the code, and generates a surgical git diff patch.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Target file path"},
                "error": {"type": "string", "description": "Crash traceback or exception message"}
            },
            "required": ["filepath", "error"]
        }
    },
    {
        "name": "git_oops_safe_exec",
        "description": "Runs a shell command through the Blast-Radius firewall, preventing destructive deletions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command line to execute"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "git_oops_squeezer",
        "description": "Compresses noisy multi-thousand line terminal output into high-density context and redacts secrets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw_logs": {"type": "string", "description": "Raw noisy logs"}
            },
            "required": ["raw_logs"]
        }
    }
]


def run_mcp_server():
    """Stdio JSON-RPC loop for Model Context Protocol agents."""
    sys.stderr.write("⚡ [GIT-OOPS MCP SERVER] Active and listening on stdio (JSON-RPC 2.0)...\n")
    sys.stderr.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "git-oops", "version": "0.2.0"}
                }
            }
        elif method == "tools/list":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": MCP_TOOLS}
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            
            if tool_name == "git_oops_safe_exec":
                cmd = args.get("command", "")
                safe, reason = check_command_safety(cmd)
                content = [{"type": "text", "text": json.dumps({"allowed": safe, "reason": reason})}]
            elif tool_name == "git_oops_squeezer":
                logs = args.get("raw_logs", "")
                compressed = compress_traceback(logs)
                content = [{"type": "text", "text": compressed}]
            elif tool_name == "git_oops_diagnose":
                fp = args.get("filepath", "")
                err = args.get("error", "")
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        code_ctx = f.read()
                    diag = diagnose_and_patch(err, code_ctx, fp)
                    content = [{"type": "text", "text": json.dumps(diag)}]
                except Exception as ex:
                    content = [{"type": "text", "text": json.dumps({"error": str(ex)})}]
            else:
                content = [{"type": "text", "text": f"Unknown tool: {tool_name}"}]

            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": content}
            }
        else:
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }

        sys.stdout.write(json.dumps(res) + "\n")
        sys.stdout.flush()
