"""Ollama local LLM discovery and model management."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any

from cli.aikit.app_home import config_path


OLLAMA_TIMEOUT_SECONDS = 120
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_RECOMMENDED_MODELS = [
    {"name": "qwen3:0.6b", "family": "mini-brain", "recommended_for": "setup help, short summaries and lightweight intent classification"},
    {"name": "qwen2.5-coder", "family": "coding", "recommended_for": "operational code reading and generation"},
    {"name": "deepseek-coder", "family": "coding", "recommended_for": "code analysis and mechanical refactors"},
    {"name": "deepseek-r1", "family": "reasoning", "recommended_for": "local reasoning drafts with mandatory review"},
    {"name": "llama3.2", "family": "general", "recommended_for": "general local summaries and classification"},
    {"name": "mistral", "family": "general", "recommended_for": "lightweight operational summaries"},
    {"name": "gemma", "family": "classification", "recommended_for": "small extraction and classification tasks"},
]


def ollama_status(*, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    base_url = os.environ.get("OLLAMA_BASE_URL") or base_url
    binary = shutil.which("ollama")
    version = command_output(["ollama", "--version"]) if binary else None
    daemon = daemon_status(base_url) if binary else {"status": "unknown", "message": "Ollama binary is not installed."}
    models = list_local_models(binary_available=bool(binary))
    status = "missing"
    if binary:
        status = "ok" if daemon.get("status") == "ok" else "partial"
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
        needs_confirmation = not dry_run and not yes
        return {
            "kind": "ollama-pull",
            "status": "planned" if dry_run else "needs-confirmation",
            "ok": bool(dry_run),
            "exit_code": 2 if needs_confirmation else 0,
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
        needs_confirmation = not dry_run and not yes
        return {
            "kind": "ollama-update",
            "status": "planned" if dry_run else "needs-confirmation",
            "ok": bool(dry_run),
            "exit_code": 2 if needs_confirmation else 0,
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
    catalog = model_catalog()
    return [
        {
            "name": item["name"],
            "family": item["family"],
            "recommended_for": item["recommended_for"],
            "installed": any(model == item["name"] or model.startswith(f"{item['name']}:") for model in installed),
            "source": item["source"],
        }
        for item in catalog
    ]


def model_catalog() -> list[dict[str, str]]:
    items = {item["name"]: {**item, "source": "default"} for item in DEFAULT_RECOMMENDED_MODELS}
    for item in configured_model_catalog():
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        items[name] = {
            "name": name,
            "family": str(item.get("family") or "custom").strip() or "custom",
            "recommended_for": str(item.get("recommended_for") or item.get("purpose") or "configured local model").strip(),
            "source": "config",
        }
    return list(items.values())


def configured_model_catalog() -> list[dict[str, Any]]:
    path = config_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, dict):
        return []
    local_llm = payload.get("local_llm") if isinstance(payload.get("local_llm"), dict) else {}
    mini_brain = payload.get("mini_brain") if isinstance(payload.get("mini_brain"), dict) else {}
    for value in (
        local_llm.get("recommended_models"),
        local_llm.get("models"),
        mini_brain.get("recommended_models"),
    ):
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


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
