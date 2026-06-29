"""Toolchain discovery and controlled install planning."""

from __future__ import annotations

import platform
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


TOOLCHAIN_PATH = Path(__file__).resolve().parents[2] / "tooling" / "toolchain.yaml"
INSTALL_TIMEOUT_SECONDS = 900


def list_toolchain(root: Path | None = None) -> dict[str, Any]:
    tools = load_toolchain(root)
    return {
        "kind": "toolchain",
        "status": "ok",
        "platform": platform_key(),
        "path": str(toolchain_path(root)),
        "items": [public_tool(tool_id, spec) for tool_id, spec in tools.items()],
    }


def doctor_toolchain(root: Path | None = None, tool_id: str | None = None) -> dict[str, Any]:
    tools = select_tools(root, tool_id)
    items = [tool_status(item_id, spec) for item_id, spec in tools.items()]
    required_missing = [item["id"] for item in items if item.get("required") and item.get("status") == "missing"]
    optional_missing = [item["id"] for item in items if not item.get("required") and item.get("status") == "missing"]
    status = "ok"
    if required_missing:
        status = "missing"
    elif optional_missing:
        status = "partial"
    return {
        "kind": "toolchain-doctor",
        "status": status,
        "platform": platform_key(),
        "path": str(toolchain_path(root)),
        "required_missing": required_missing,
        "optional_missing": optional_missing,
        "items": items,
    }


def install_toolchain(
    root: Path | None = None,
    tool_id: str | None = None,
    *,
    dry_run: bool = False,
    yes: bool = False,
) -> dict[str, Any]:
    tools = select_tools(root, tool_id)
    platform_name = platform_key()
    plans = []
    for item_id, spec in tools.items():
        current_status = tool_status(item_id, spec)
        already_installed = current_status.get("status") == "ok"
        command = None if already_installed else install_command(spec, platform_name)
        plans.append(
            {
                "id": item_id,
                "label": spec.get("label") or item_id,
                "command": command,
                "status": "already-installed" if already_installed else "planned",
                "binary": current_status.get("binary"),
                "executable": is_executable_install_command(command),
            }
        )

    if dry_run:
        return install_payload("planned", plans, dry_run=True, yes=yes, executed=[])
    if not yes:
        return install_payload(
            "needs-confirmation",
            plans,
            dry_run=False,
            yes=False,
            executed=[],
            message="External tool installation requires --yes. Use --dry-run to inspect the plan.",
        )

    executed: list[dict[str, Any]] = []
    for plan in plans:
        if plan["status"] == "already-installed":
            executed.append({**plan, "status": "already-installed", "message": "Tool already available in PATH."})
            continue
        if not plan["executable"]:
            executed.append({**plan, "status": "skipped", "message": "Manual installation instruction."})
            continue
        process = subprocess.run(
            str(plan["command"]),
            shell=True,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=INSTALL_TIMEOUT_SECONDS,
        )
        executed.append(
            {
                **plan,
                "status": "installed" if process.returncode == 0 else "failed",
                "exit_code": process.returncode,
                "stdout": safe_tail(redact_environment_secrets(process.stdout)),
                "stderr": safe_tail(redact_environment_secrets(process.stderr)),
            }
        )
    status = "installed" if all(item["status"] in {"installed", "skipped", "already-installed"} for item in executed) else "failed"
    return install_payload(status, plans, dry_run=False, yes=True, executed=executed)


def setup_plan(root: Path | None = None, *, dry_run: bool = False, yes: bool = False) -> dict[str, Any]:
    doctor = doctor_toolchain(root)
    if yes and not dry_run:
        install = install_toolchain(root, "all", dry_run=False, yes=True)
    else:
        install = install_toolchain(root, "all", dry_run=True, yes=yes)
    status = install["status"] if yes and not dry_run else "planned"
    return {
        "kind": "setup",
        "status": status,
        "dry_run": dry_run,
        "yes": yes,
        "toolchain": doctor,
        "install_plan": install["plans"],
        "install": install,
        "next_steps": [
            "Run `agent toolchain doctor` to inspect local dependencies.",
            "Run `agent toolchain install <tool> --dry-run` before installing external tools.",
            "Use `agent setup personality` to configure local identity and style.",
        ],
    }


def install_payload(
    status: str,
    plans: list[dict[str, Any]],
    *,
    dry_run: bool,
    yes: bool,
    executed: list[dict[str, Any]],
    message: str | None = None,
) -> dict[str, Any]:
    payload = {
        "kind": "toolchain-install",
        "status": status,
        "platform": platform_key(),
        "dry_run": dry_run,
        "yes": yes,
        "stored_secret": False,
        "plans": plans,
        "executed": executed,
    }
    if message:
        payload["message"] = message
    return payload


def load_toolchain(root: Path | None = None) -> dict[str, dict[str, Any]]:
    path = toolchain_path(root)
    if not path.exists():
        return fallback_toolchain()
    try:
        import yaml  # type: ignore
    except ImportError:
        return fallback_toolchain()
    try:
        with path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except OSError:
        return fallback_toolchain()
    tools = data.get("tools") if isinstance(data, dict) else {}
    if not isinstance(tools, dict):
        return {}
    return {str(key): value for key, value in tools.items() if isinstance(value, dict)}


def fallback_toolchain() -> dict[str, dict[str, Any]]:
    return {
        "node": {"label": "Node.js", "command": "node", "required": True, "install": {}},
        "python": {"label": "Python", "command": "python3", "required": True, "install": {}},
        "git": {"label": "Git", "command": "git", "required": True, "install": {}},
    }


def select_tools(root: Path | None, tool_id: str | None) -> dict[str, dict[str, Any]]:
    tools = load_toolchain(root)
    if not tool_id or tool_id == "all":
        return tools
    if tool_id not in tools:
        available = ", ".join(sorted(tools)) or "none"
        raise ValueError(f"unknown toolchain item: {tool_id}. available: {available}")
    return {tool_id: tools[tool_id]}


def public_tool(tool_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": tool_id,
        "label": spec.get("label") or tool_id,
        "command": spec.get("command"),
        "required": bool(spec.get("required")),
        "install": install_command(spec, platform_key()),
        "notes": spec.get("notes"),
    }


def tool_status(tool_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    command = str(spec.get("command") or "")
    binary = shutil.which(command) if command else None
    return {
        **public_tool(tool_id, spec),
        "status": "ok" if binary else "missing",
        "binary": binary,
        "version": read_version(binary),
    }


def read_version(binary: str | None) -> str | None:
    if not binary:
        return None
    for args in ([binary, "--version"], [binary, "version"]):
        try:
            process = subprocess.run(args, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            continue
        output = (process.stdout or process.stderr or "").strip()
        if output:
            return output.splitlines()[0]
    return None


def install_command(spec: dict[str, Any], platform_name: str) -> str | None:
    install = spec.get("install")
    if not isinstance(install, dict):
        return None
    command = install.get(platform_name) or install.get("default")
    return str(command) if command else None


def is_executable_install_command(command: str | None) -> bool:
    if not command:
        return False
    manual_prefixes = ("See ", "Configure ", "Use ", "Open ", "Install manually")
    return not command.startswith(manual_prefixes)


def platform_key() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    if system.startswith("win"):
        return "windows"
    return "linux"


def toolchain_path(root: Path | None = None) -> Path:
    if root:
        return root / "tooling" / "toolchain.yaml"
    return TOOLCHAIN_PATH


def safe_tail(value: str, limit: int = 2000) -> str:
    text = value or ""
    return text[-limit:]


def redact_environment_secrets(value: str) -> str:
    redacted = value or ""
    for key, secret in os.environ.items():
        if not secret:
            continue
        if not any(marker in key.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS", "PAT")):
            continue
        redacted = redacted.replace(secret, "[REDACTED]")
    return redacted
