"""Ollama local LLM discovery and model management."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any


OLLAMA_TIMEOUT_SECONDS = 120
DEFAULT_BASE_URL = "http://localhost:11434"


def ollama_status(*, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    binary = shutil.which("ollama")
    version = command_output(["ollama", "--version"]) if binary else None
    daemon = daemon_status(base_url) if binary else {"status": "unknown", "message": "Ollama binary is not installed."}
    models = list_local_models(binary_available=bool(binary))
    status = "ok" if binary else "missing"
    return {
        "kind": "ollama-status",
        "status": status,
        "binary": binary,
        "version": first_line(version),
        "base_url": base_url,
        "daemon": daemon,
        "models": models,
        "model_count": len(models),
        "install_plan": install_plan() if not binary else None,
    }


def ollama_models() -> dict[str, Any]:
    binary = shutil.which("ollama")
    items = list_local_models(binary_available=bool(binary))
    return {
        "kind": "ollama-models",
        "status": "ok" if binary else "missing",
        "binary": binary,
        "items": items,
        "recommended": recommended_models(installed={item["name"] for item in items}),
    }


def ollama_pull(model: str | None, *, yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not model:
        raise ValueError("ollama pull requires a model name")
    binary = shutil.which("ollama")
    command = ["ollama", "pull", model]
    if dry_run or not yes:
        return {
            "kind": "ollama-pull",
            "status": "planned" if dry_run else "needs-confirmation",
            "ok": bool(dry_run),
            "model": model,
            "binary": binary,
            "command": command,
            "dry_run": dry_run,
            "yes": yes,
            "message": "Use --yes to pull the model." if not dry_run and not yes else "Dry-run only.",
        }
    if not binary:
        return {
            "kind": "ollama-pull",
            "status": "missing",
            "ok": False,
            "model": model,
            "command": command,
            "message": "Ollama binary not found in PATH.",
            "install_plan": install_plan(),
            "exit_code": 2,
        }
    process = run_command(command, timeout=OLLAMA_TIMEOUT_SECONDS * 5)
    return {
        "kind": "ollama-pull",
        "status": "ok" if process.returncode == 0 else "failed",
        "ok": process.returncode == 0,
        "model": model,
        "binary": binary,
        "command": command,
        "exit_code": process.returncode,
        "stdout": safe_tail(process.stdout),
        "stderr": safe_tail(process.stderr),
    }


def ollama_update(*, yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    command = update_command()
    if dry_run or not yes:
        return {
            "kind": "ollama-update",
            "status": "planned" if dry_run else "needs-confirmation",
            "ok": bool(dry_run),
            "command": command,
            "dry_run": dry_run,
            "yes": yes,
            "message": "Use --yes to run the update command." if not dry_run and not yes else "Dry-run only.",
        }
    process = run_command(command, timeout=OLLAMA_TIMEOUT_SECONDS * 5, shell=True)
    return {
        "kind": "ollama-update",
        "status": "ok" if process.returncode == 0 else "failed",
        "ok": process.returncode == 0,
        "command": command,
        "exit_code": process.returncode,
        "stdout": safe_tail(process.stdout),
        "stderr": safe_tail(process.stderr),
    }


def list_local_models(*, binary_available: bool) -> list[dict[str, Any]]:
    if not binary_available:
        return []
    output = command_output(["ollama", "list"])
    if not output:
        return []
    return parse_ollama_list(output)


def parse_ollama_list(output: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("name "):
            continue
        parts = stripped.split()
        if not parts:
            continue
        items.append(
            {
                "name": parts[0],
                "id": parts[1] if len(parts) > 1 else None,
                "size": parts[2] if len(parts) > 2 else None,
                "modified": " ".join(parts[3:]) if len(parts) > 3 else None,
            }
        )
    return items


def recommended_models(*, installed: set[str]) -> list[dict[str, Any]]:
    catalog = [
        ("qwen3:0.6b", "mini-brain", "setup help, short summaries and lightweight intent classification"),
        ("qwen2.5-coder", "coding", "operational code reading and generation"),
        ("deepseek-coder", "coding", "code analysis and mechanical refactors"),
        ("deepseek-r1", "reasoning", "local reasoning drafts with mandatory review"),
        ("llama3.2", "general", "general local summaries and classification"),
        ("mistral", "general", "lightweight operational summaries"),
        ("gemma", "classification", "small extraction and classification tasks"),
    ]
    return [
        {
            "name": name,
            "family": family,
            "recommended_for": recommended_for,
            "installed": any(item == name or item.startswith(f"{name}:") for item in installed),
        }
        for name, family, recommended_for in catalog
    ]


def daemon_status(base_url: str) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=2) as response:  # noqa: S310 - local configurable daemon URL.
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        return {"status": "unavailable", "message": str(exc.reason)}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"status": "unknown", "message": "Ollama daemon returned non-JSON response."}
    return {"status": "ok", "models": len(payload.get("models") or []) if isinstance(payload, dict) else None}


def install_plan() -> dict[str, Any]:
    system = platform.system().lower()
    if system == "darwin":
        command = "brew install ollama"
    elif system.startswith("win"):
        command = "winget install Ollama.Ollama"
    else:
        command = "curl -fsSL https://ollama.com/install.sh | sh"
    return {"platform": platform_key(), "command": command, "requires_opt_in": True}


def update_command() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "brew upgrade ollama"
    if system.startswith("win"):
        return "winget upgrade Ollama.Ollama"
    return "curl -fsSL https://ollama.com/install.sh | sh"


def platform_key() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    if system.startswith("win"):
        return "windows"
    return "linux"


def command_output(command: list[str]) -> str | None:
    try:
        process = run_command(command, timeout=10)
    except OSError:
        return None
    if process.returncode != 0:
        return None
    return process.stdout.strip() or process.stderr.strip()


def run_command(command: list[str] | str, *, timeout: int, shell: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        shell=shell,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def safe_tail(value: str | None, *, limit: int = 4000) -> str:
    text = value or ""
    return text[-limit:]


def first_line(value: str | None) -> str | None:
    if not value:
        return None
    return value.splitlines()[0]
