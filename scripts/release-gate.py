#!/usr/bin/env python3
"""Run the AI DevKit release gate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agent"
VALIDATE_REPO = ROOT / "scripts" / "validate-repo.py"
MVP_READINESS = ROOT / "scripts" / "mvp-readiness.py"
CLAUDE_SKILL = ROOT / "plugins" / "claude-skill-ai-devkit" / "ai-devkit"
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
SKILL_VALIDATOR = CODEX_HOME / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AI DevKit release gate checks.")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--quick", action="store_true", help="skip the full unittest suite")
    args = parser.parse_args()

    payload = run_gate(quick=args.quick)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human(payload)
    return 0 if payload["status"] == "ok" else 1


def run_gate(*, quick: bool = False) -> dict[str, Any]:
    checks = [
        check_command("agent version", [sys.executable, str(AGENT), "--version"], validate_agent_version),
        check_json("repo strict validation", [sys.executable, str(VALIDATE_REPO), "--strict", "--json"], validate_repo),
        check_json("mvp readiness", [sys.executable, str(MVP_READINESS), "--json"], validate_mvp_readiness),
        skill_validation_check(),
    ]
    if quick:
        checks.append(skipped_check("full unittest suite", "skipped by --quick"))
    else:
        checks.append(check_command("full unittest suite", unittest_command(), validate_unittest))

    errors = [check["message"] for check in checks if check["status"] == "failed"]
    return {
        "kind": "release-gate",
        "status": "ok" if not errors else "failed",
        "quick": quick,
        "checks": checks,
        "errors": errors,
    }


def skill_validation_check() -> dict[str, Any]:
    if not SKILL_VALIDATOR.exists():
        return skipped_check("claude skill validation", f"skill validator not found at {SKILL_VALIDATOR}")
    return check_command(
        "claude skill validation",
        [sys.executable, str(SKILL_VALIDATOR), str(CLAUDE_SKILL)],
        validate_skill_validation,
    )


def unittest_command() -> list[str]:
    paths = [
        path
        for path in ROOT.rglob("test*.py")
        if "vendor" not in path.relative_to(ROOT).parts
    ]
    paths.sort(key=unittest_path_sort_key)
    test_files = [str(path.relative_to(ROOT)) for path in paths]
    return [sys.executable, "-m", "unittest", *test_files]


def unittest_path_sort_key(path: Path) -> tuple[int, str]:
    relative = path.relative_to(ROOT)
    first = relative.parts[0] if relative.parts else ""
    return (0 if first == "tests" else 1, str(relative))


def check_json(name: str, command: list[str], validator) -> dict[str, Any]:
    result = run(command)
    if result.returncode != 0:
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


def check_command(name: str, command: list[str], validator) -> dict[str, Any]:
    result = run(command)
    if result.returncode != 0:
        return failed_check(name, f"returncode {result.returncode}", result)
    message = validator(result)
    if message:
        return failed_check(name, message, result)
    return ok_check(name, result)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=360,
    )


def validate_agent_version(result: subprocess.CompletedProcess[str]) -> str | None:
    if not result.stdout.startswith("agent "):
        return "agent --version did not report the agent command"
    return None


def validate_repo(payload: dict[str, Any]) -> str | None:
    if payload.get("errors"):
        return "validate-repo returned errors"
    if payload.get("warnings"):
        return "validate-repo returned warnings"
    summary = payload.get("summary") or {}
    if summary.get("agents", 0) < 1 or summary.get("capabilities", 0) < 1:
        return "validate-repo summary is missing agents or capabilities"
    if summary.get("plugins", 0) < 3:
        return "validate-repo did not report all MVP plugins"
    return None


def validate_mvp_readiness(payload: dict[str, Any]) -> str | None:
    if payload.get("kind") != "mvp-readiness" or payload.get("status") != "ok":
        return "mvp readiness is not ok"
    if payload.get("errors"):
        return "mvp readiness returned errors"
    return None


def validate_skill_validation(result: subprocess.CompletedProcess[str]) -> str | None:
    if "Skill is valid!" not in result.stdout:
        return "Claude Desktop skill validation did not report success"
    return None


def validate_unittest(result: subprocess.CompletedProcess[str]) -> str | None:
    output = f"{result.stdout}\n{result.stderr}"
    if "OK" not in output:
        return "unittest suite did not report OK"
    return None


def summarize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    summary = {
        key: payload[key]
        for key in ("kind", "status")
        if key in payload
    }
    if isinstance(payload.get("summary"), dict):
        summary["summary"] = payload["summary"]
    return summary


def ok_check(name: str, result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "name": name,
        "status": "ok",
        "returncode": result.returncode,
        "message": "",
    }


def failed_check(name: str, message: str, result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "name": name,
        "status": "failed",
        "returncode": result.returncode,
        "message": message,
        "stdout": trim(result.stdout),
        "stderr": trim(result.stderr),
    }


def skipped_check(name: str, message: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": "skipped",
        "returncode": None,
        "message": message,
    }


def trim(value: str, limit: int = 6000) -> str:
    value = value.strip()
    return value if len(value) <= limit else value[:limit] + "..."


def print_human(payload: dict[str, Any]) -> None:
    print(f"AI DevKit release gate: {payload['status']}")
    for check in payload["checks"]:
        print(f"- {check['status']}: {check['name']}")
        if check.get("message"):
            print(f"  {check['message']}")


if __name__ == "__main__":
    raise SystemExit(main())
