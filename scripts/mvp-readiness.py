#!/usr/bin/env python3
"""Run local MVP readiness checks without external network calls."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agent"
REQUIRED_MVP_PROVIDERS = {
    "aws",
    "azure-devops",
    "bpo",
    "elasticsearch",
    "figma",
    "postgres",
    "sqlserver",
    "technical-http",
    "topdesk",
}
REQUIRED_MVP_LLM_BACKENDS = {
    "openai",
    "anthropic",
    "openrouter",
    "ollama",
    "codex-cli",
    "claude-code",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check AI DevKit MVP readiness.")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()

    payload = run_readiness()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human(payload)
    return 0 if payload["status"] == "ok" else 1


def run_readiness() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    with (
        tempfile.TemporaryDirectory() as project_dir,
        tempfile.TemporaryDirectory() as config_home,
        tempfile.TemporaryDirectory() as install_home,
    ):
        env = isolated_env(Path(config_home), Path(install_home))
        project = Path(project_dir)

        checks.append(check_command("agent version", [sys.executable, str(AGENT), "--version"], env))
        checks.append(
            check_json(
                "commands list",
                [sys.executable, str(AGENT), "--json", "commands", "list"],
                env,
                validate_commands,
            )
        )
        checks.append(
            check_json(
                "llm backends list",
                [sys.executable, str(AGENT), "--json", "llm", "list"],
                env,
                validate_llm_backends,
            )
        )
        checks.append(
            check_json(
                "providers list",
                [sys.executable, str(AGENT), "--json", "providers", "list"],
                env,
                validate_providers,
            )
        )
        checks.append(
            check_json(
                "project install",
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "install",
                    "project",
                    "--target",
                    str(project),
                    "--host",
                    "all",
                ],
                env,
                validate_install,
            )
        )
        checks.append(
            check_json(
                "doctor clean project",
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "doctor",
                    "--project",
                    str(project),
                    "--home",
                    str(install_home),
                ],
                env,
                validate_doctor,
            )
        )
        checks.append(
            check_json(
                "run fallback without provider",
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "elasticsearch-log-analyzer",
                    "search-log-events",
                    "--source",
                    "app-logs",
                    "--from",
                    "2026-06-27T00:00:00Z",
                    "--to",
                    "2026-06-27T01:00:00Z",
                ],
                env,
                validate_plan_only_fallback,
            )
        )
        checks.append(
            check_json(
                "agent without llm",
                [sys.executable, str(AGENT), "--json", "analise esse incidente"],
                env,
                validate_agent_without_llm,
                expected_returncodes={2},
            )
        )
        checks.append(
            check_json(
                "repo strict validation",
                [sys.executable, str(ROOT / "scripts" / "validate-repo.py"), "--strict", "--json"],
                env,
                validate_repo_strict,
            )
        )

    errors = [check["message"] for check in checks if check["status"] != "ok"]
    return {
        "kind": "mvp-readiness",
        "status": "ok" if not errors else "failed",
        "checks": checks,
        "errors": errors,
        "warnings": [],
    }


def isolated_env(config_home: Path, install_home: Path) -> dict[str, str]:
    return {
        "AIKIT_CONFIG_HOME": str(config_home),
        "AIKIT_INSTALL_HOME": str(install_home),
        "PATH": os.environ.get("PATH", ""),
    }


def check_command(name: str, command: list[str], env: dict[str, str]) -> dict[str, Any]:
    result = run(command, env)
    if result.returncode != 0:
        return failed_check(name, f"returncode {result.returncode}", result)
    return ok_check(name, result)


def check_json(
    name: str,
    command: list[str],
    env: dict[str, str],
    validator,
    *,
    expected_returncodes: set[int] | None = None,
) -> dict[str, Any]:
    result = run(command, env)
    expected = expected_returncodes or {0}
    if result.returncode not in expected:
        return failed_check(name, f"returncode {result.returncode}", result)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return failed_check(name, f"invalid json: {exc}", result)
    message = validator(payload)
    if message:
        return failed_check(name, message, result)
    check = ok_check(name, result)
    check["summary"] = summarize_payload(payload)
    return check


def run(command: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )


def ok_check(name: str, result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {"name": name, "status": "ok", "returncode": result.returncode, "message": ""}


def failed_check(name: str, message: str, result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "name": name,
        "status": "failed",
        "returncode": result.returncode,
        "message": message,
        "stderr": trim(result.stderr),
        "stdout": trim(result.stdout),
    }


def trim(value: str, limit: int = 500) -> str:
    value = value.strip()
    return value if len(value) <= limit else value[:limit] + "..."


def summarize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: payload[key]
        for key in ("kind", "status", "fallback_applied")
        if key in payload
    }


def validate_commands(payload: dict[str, Any]) -> str | None:
    deterministic = {item.get("command") for item in payload.get("deterministic", [])}
    llm = {item.get("command") for item in payload.get("llm", [])}
    required = {"run", "doctor", "providers", "provider", "credential", "install", "llm"}
    missing = sorted(required - deterministic)
    if missing:
        return f"missing deterministic commands: {', '.join(missing)}"
    if "agent" not in llm:
        return "missing llm command: agent"
    return None


def validate_providers(payload: dict[str, Any]) -> str | None:
    providers = {item.get("id") for item in payload.get("items", [])}
    missing = sorted(REQUIRED_MVP_PROVIDERS - providers)
    if missing:
        return f"missing MVP providers: {', '.join(missing)}"
    return None


def validate_llm_backends(payload: dict[str, Any]) -> str | None:
    if payload.get("kind") != "llm-backends":
        return "llm list returned unexpected payload"
    backends = {item.get("id") for item in payload.get("items", [])}
    missing = sorted(REQUIRED_MVP_LLM_BACKENDS - backends)
    if missing:
        return f"missing MVP LLM backends: {', '.join(missing)}"
    return None


def validate_install(payload: dict[str, Any]) -> str | None:
    if payload.get("kind") != "install" or payload.get("status") != "installed":
        return "install did not complete"
    if payload.get("stored_secret"):
        return "install reported stored_secret=true"
    hosts = set(payload.get("hosts", []))
    if hosts != {"codex", "claude-code", "claude-desktop"}:
        return f"unexpected hosts: {sorted(hosts)}"
    for key in ("config_path", "lock_path"):
        path = Path(str(payload.get(key) or ""))
        if not path.exists():
            return f"{key} does not exist: {path}"
    target = Path(str(payload.get("target") or ""))
    plugin_paths = (
        target / ".codex" / "plugins" / "ai-devkit",
        target / ".claude" / "plugins" / "ai-devkit",
        target / ".claude" / "skills" / "ai-devkit",
    )
    for path in plugin_paths:
        if not path.exists():
            return f"installed plugin path does not exist: {path}"
    return None


def validate_doctor(payload: dict[str, Any]) -> str | None:
    if payload.get("kind") != "doctor" or payload.get("status") != "ok":
        return "doctor status is not ok"
    diagnostics = payload.get("diagnostics") or {}
    if (
        "providers" not in diagnostics
        or "llm" not in diagnostics
        or "plugins" not in diagnostics
    ):
        return "doctor missing expanded diagnostics"
    plugins = diagnostics.get("plugins") or {}
    if plugins.get("status") != "ok":
        return f"doctor plugins status is not ok: {plugins.get('status')}"
    return None


def validate_plan_only_fallback(payload: dict[str, Any]) -> str | None:
    if payload.get("kind") != "run" or payload.get("status") != "partial":
        return "run did not return partial fallback"
    providers = payload.get("providers") or {}
    if providers.get("missing") != ["elasticsearch"]:
        return "fallback did not report missing elasticsearch"
    if payload.get("fallback_applied") != "plan_only":
        return "fallback_applied is not plan_only"
    return None


def validate_agent_without_llm(payload: dict[str, Any]) -> str | None:
    if payload.get("kind") != "agent" or payload.get("status") != "blocked":
        return "agent without llm did not block instructively"
    if not payload.get("requires_llm"):
        return "agent payload missing requires_llm=true"
    return None


def validate_repo_strict(payload: dict[str, Any]) -> str | None:
    if payload.get("errors"):
        return "strict validation returned errors"
    if payload.get("warnings"):
        return "strict validation returned warnings"
    summary = payload.get("summary") or {}
    if summary.get("providers", 0) < len(REQUIRED_MVP_PROVIDERS):
        return "provider count below MVP provider minimum"
    return None


def print_human(payload: dict[str, Any]) -> None:
    print(f"AI DevKit MVP readiness: {payload['status']}")
    for check in payload["checks"]:
        print(f"- {check['status']}: {check['name']}")
        if check.get("message"):
            print(f"  {check['message']}")


if __name__ == "__main__":
    raise SystemExit(main())
