"""Canonical local-LLM CLI surface over Ollama and mini-brain policy."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from cli.aikit.embedded_mini_brain import EMBEDDED_BACKEND_ID, EMBEDDED_MODEL_ID, embedded_mini_brain_status
from cli.aikit.mini_brain import DEFAULT_OLLAMA_MODEL, mini_brain_contract
from cli.aikit.model_router import build_model_plan
from cli.aikit.ollama import ollama_models, ollama_pull, ollama_status


LOCAL_LLM_SCHEMA_VERSION = "agent-devkit.local-llm/v1"
LOCAL_WORKERS = (
    ("local-classifier", "intent classification and routing hints"),
    ("local-summarizer", "short summaries and extraction"),
    ("local-coder", "mechanical code drafts with coordinator review"),
    ("local-log-analyzer", "log clustering and evidence extraction"),
    ("local-sql-helper", "SQL draft assistance with review required"),
)


def local_llm_list() -> dict[str, Any]:
    status = ollama_status()
    contract = mini_brain_contract(ollama_payload=status)
    return {
        "kind": "local-llm",
        "schema_version": LOCAL_LLM_SCHEMA_VERSION,
        "status": "ok",
        "provider": EMBEDDED_BACKEND_ID,
        "optional_providers": ["ollama"],
        "embedded": embedded_mini_brain_status(),
        "mini_brain": contract,
        "workers": [{"id": worker_id, "purpose": purpose} for worker_id, purpose in LOCAL_WORKERS],
        "models": {
            "status": status.get("status"),
            "count": status.get("model_count", 0),
        },
    }


def local_llm_doctor() -> dict[str, Any]:
    status = ollama_status()
    contract = mini_brain_contract(ollama_payload=status)
    model_plan = build_model_plan("resuma estes logs operacionais")
    ok = contract.get("available") is True
    return {
        "kind": "local-llm-doctor",
        "schema_version": LOCAL_LLM_SCHEMA_VERSION,
        "status": "ok" if ok else "partial",
        "provider": EMBEDDED_BACKEND_ID,
        "optional_providers": ["ollama"],
        "embedded": embedded_mini_brain_status(),
        "ollama": status,
        "mini_brain": contract,
        "model_plan": {
            "strategy": model_plan.get("strategy"),
            "local_llm_recommended": model_plan.get("local_llm_recommended"),
            "local_llm_selected": model_plan.get("local_llm_selected"),
            "local_llm_role": model_plan.get("local_llm_role"),
            "forbidden_actions": model_plan.get("forbidden_actions") or [],
        },
        "next_steps": local_llm_next_steps(status=status, mini_brain=contract),
    }


def local_llm_models() -> dict[str, Any]:
    payload = ollama_models()
    embedded = embedded_mini_brain_status()
    payload["kind"] = "local-llm-models"
    payload["schema_version"] = LOCAL_LLM_SCHEMA_VERSION
    payload["provider"] = EMBEDDED_BACKEND_ID
    payload["embedded"] = {
        "status": embedded.get("status"),
        "provider": EMBEDDED_BACKEND_ID,
        "model": EMBEDDED_MODEL_ID,
        "installed": embedded.get("model_file_valid") is True,
        "available": embedded.get("available") is True,
        "install_command": embedded.get("install_command"),
    }
    payload["optional_provider"] = "ollama"
    return payload


def local_llm_install(model: str | None, *, dry_run: bool = False, yes: bool = False) -> dict[str, Any]:
    model = model or DEFAULT_OLLAMA_MODEL
    payload = ollama_pull(model, dry_run=dry_run, yes=yes)
    payload["kind"] = "local-llm-install"
    payload["schema_version"] = LOCAL_LLM_SCHEMA_VERSION
    payload["provider"] = "ollama"
    return payload


def local_llm_remove(model: str | None, *, dry_run: bool = False, yes: bool = False) -> dict[str, Any]:
    model = model or DEFAULT_OLLAMA_MODEL
    command = ["ollama", "rm", model]
    binary = shutil.which("ollama")
    if dry_run or not yes:
        needs_confirmation = not dry_run and not yes
        return {
            "kind": "local-llm-remove",
            "schema_version": LOCAL_LLM_SCHEMA_VERSION,
            "status": "planned" if dry_run else "needs-confirmation",
            "ok": bool(dry_run),
            "exit_code": 2 if needs_confirmation else 0,
            "provider": "ollama",
            "model": model,
            "binary": binary,
            "command": command,
            "dry_run": dry_run,
            "yes": yes,
            "message": "Use --yes to remove the local model." if not dry_run and not yes else "Dry-run only.",
        }
    if not binary:
        return {
            "kind": "local-llm-remove",
            "schema_version": LOCAL_LLM_SCHEMA_VERSION,
            "status": "missing",
            "ok": False,
            "provider": "ollama",
            "model": model,
            "command": command,
            "message": "Ollama binary not found in PATH.",
            "exit_code": 2,
        }
    process = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    return {
        "kind": "local-llm-remove",
        "schema_version": LOCAL_LLM_SCHEMA_VERSION,
        "status": "ok" if process.returncode == 0 else "failed",
        "ok": process.returncode == 0,
        "provider": "ollama",
        "model": model,
        "binary": binary,
        "command": command,
        "exit_code": process.returncode,
        "stdout": process.stdout[-4000:],
        "stderr": process.stderr[-4000:],
    }


def local_llm_benchmark(model: str | None = None) -> dict[str, Any]:
    model = model or DEFAULT_OLLAMA_MODEL
    status = ollama_status()
    installed = {item.get("name") for item in status.get("models") or [] if isinstance(item, dict)}
    available = status.get("status") == "ok" and model in installed
    return {
        "kind": "local-llm-benchmark",
        "schema_version": LOCAL_LLM_SCHEMA_VERSION,
        "status": "ready" if available else "planned",
        "ok": available,
        "provider": "ollama",
        "model": model,
        "checks": [
            {"id": "ollama-binary", "status": "passed" if status.get("status") == "ok" else "failed"},
            {"id": "model-installed", "status": "passed" if model in installed else "planned"},
            {"id": "policy", "status": "passed", "message": "Benchmark is read-only and does not approve final work."},
        ],
        "next_steps": [] if available else [f"agent local-llm install {model} --yes"],
    }


def local_llm_next_steps(*, status: dict[str, Any], mini_brain: dict[str, Any]) -> list[str]:
    steps: list[str] = []
    if status.get("status") != "ok":
        install_plan = status.get("install_plan") if isinstance(status.get("install_plan"), dict) else {}
        command = install_plan.get("command")
        if command:
            steps.append(f"Install Ollama: {command}")
    if not mini_brain.get("enabled"):
        steps.append("agent setup mini-brain --yes")
    if status.get("model_count", 0) < 1:
        steps.append(f"agent local-llm install {DEFAULT_OLLAMA_MODEL} --yes")
    return steps
