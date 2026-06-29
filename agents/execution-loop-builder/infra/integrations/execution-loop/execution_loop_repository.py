"""Repository for deterministic execution loop planning and generation."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


LOOP_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
CAPABILITY_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*\.[a-z0-9][a-z0-9-]*$")
DESTRUCTIVE_PATTERN = re.compile(
    r"\b(rm\s+-rf|delete|drop\s+table|truncate|destroy|terraform\s+destroy|kubectl\s+delete)\b",
    re.IGNORECASE,
)
SECRET_PATTERN = re.compile(
    r"\b(SECRET|TOKEN|PASSWORD|PASS|API_KEY|PRIVATE_KEY|ACCESS_KEY)\b\s*[:=]",
    re.IGNORECASE,
)
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class ExecutionLoopBuilderError(RuntimeError):
    """Raised when a loop spec cannot be processed safely."""


class ExecutionLoopRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[5]

    def plan_execution_loop(self, *, spec_path: Path) -> dict[str, Any]:
        spec = self.load_spec(spec_path)
        result = self.validate_spec(spec)
        if result["status"] != "ok":
            return result
        normalized = self.normalize_spec(spec)
        findings = self.review_normalized_spec(normalized)
        blocking = [finding for finding in findings if finding["severity"] == "critical"]
        if blocking:
            return {
                "kind": "execution-loop-plan",
                "status": "blocked",
                "reason": "safety_guardrail_failed",
                "write_policy": "read_only",
                "findings": blocking,
            }
        return {
            "kind": "execution-loop-plan",
            "status": "ok",
            "write_policy": "read_only",
            "loop": self.loop_summary(normalized),
            "contract": normalized,
            "safety_findings": findings,
            "planned_artifacts": self.public_file_plan(self.build_loop_files(normalized)),
            "questions": self.open_questions(normalized),
        }

    def generate_loop_runner(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_execution_loop(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan
        normalized = self.normalize_spec(self.load_spec(spec_path))
        content = self.render_loop_runner(normalized)
        return {
            "kind": "execution-loop-runner",
            "status": "ok",
            "artifact": "loop_runner.py",
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "write_policy": "output_only",
        }

    def generate_loop_project_files(
        self,
        *,
        spec_path: Path,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_execution_loop(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan
        normalized = self.normalize_spec(self.load_spec(spec_path))
        target_project = normalized.get("target_project")
        if not target_project:
            return {
                "kind": "execution-loop-project-files",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }
        target_root = Path(str(target_project)).expanduser().resolve()
        return self.write_or_plan_files(
            kind="execution-loop-project-files",
            files=self.build_loop_files(normalized),
            target_root=target_root,
            execute=execute,
            allow_overwrite=allow_overwrite,
            extra={"loop": self.loop_summary(normalized), "write_policy": "local_write"},
        )

    def review_loop_safety(self, *, spec_path: Path | None = None, text: str | None = None) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        normalized: dict[str, Any] | None = None
        if spec_path is not None:
            spec = self.load_spec(spec_path)
            result = self.validate_spec(spec)
            if result["status"] != "ok":
                findings.extend(self.findings_from_validation(result))
            else:
                normalized = self.normalize_spec(spec)
                findings.extend(self.review_normalized_spec(normalized))
        if text is not None:
            findings.extend(self.review_text(text))
        valid = not any(finding["severity"] in {"critical", "high"} for finding in findings)
        return {
            "kind": "execution-loop-safety-review",
            "status": "ok" if valid else "failed",
            "valid": valid,
            "write_policy": "read_only",
            "loop": self.loop_summary(normalized) if normalized else None,
            "findings_count": len(findings),
            "findings": self.dedupe_findings(findings),
        }

    def register_loop_task(self, *, spec_path: Path, execute: bool = False) -> dict[str, Any]:
        plan = self.plan_execution_loop(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan
        normalized = self.normalize_spec(self.load_spec(spec_path))
        task_payload = self.scheduler_task_payload(normalized)
        if not execute:
            return {
                "kind": "execution-loop-task-registration",
                "status": "planned",
                "dry_run": True,
                "write_policy": "local_write",
                "loop": self.loop_summary(normalized),
                "task": task_payload,
                "next_steps": ["Rerun with --execute after reviewing the local scheduler task."],
            }
        if str(self.root) not in sys.path:
            sys.path.insert(0, str(self.root))
        try:
            from cli.aikit.tasks import create_task
        except ImportError as exc:
            raise ExecutionLoopBuilderError("cannot import local scheduler task API") from exc
        task_result = create_task(**task_payload)
        return {
            "kind": "execution-loop-task-registration",
            "status": "registered",
            "dry_run": False,
            "write_policy": "local_write",
            "loop": self.loop_summary(normalized),
            "task": task_result.get("task"),
            "path": task_result.get("path"),
        }

    def load_spec(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise ExecutionLoopBuilderError(f"spec not found: {path}")
        text = path.read_text(encoding="utf-8")
        payload = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text) or {}
        if not isinstance(payload, dict):
            raise ExecutionLoopBuilderError("spec must be a mapping")
        return payload

    def validate_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        missing = [
            field
            for field in ("id", "objective", "trigger", "budget", "side_effects", "steps", "success_when", "stop_when")
            if spec.get(field) in (None, "", [], {})
        ]
        if missing:
            return {
                "kind": "execution-loop-plan",
                "status": "needs-input",
                "missing_fields": missing,
                "questions": [self.question_for_missing_field(field) for field in missing],
            }
        loop_id = str(spec.get("id") or "").strip()
        if not LOOP_ID_PATTERN.fullmatch(loop_id):
            return {"kind": "execution-loop-plan", "status": "blocked", "reason": "invalid_loop_id"}
        for field in ("trigger", "budget", "side_effects"):
            if not isinstance(spec.get(field), dict):
                return {"kind": "execution-loop-plan", "status": "blocked", "reason": "invalid_mapping_field", "field": field}
        for field in ("steps", "success_when", "stop_when"):
            if not isinstance(spec.get(field), list) or not spec.get(field):
                return {"kind": "execution-loop-plan", "status": "blocked", "reason": "invalid_list_field", "field": field}
        budget = spec["budget"]
        for field in ("max_iterations", "max_runtime_seconds"):
            value = self.positive_int(budget.get(field))
            if value is None:
                return {"kind": "execution-loop-plan", "status": "blocked", "reason": "missing_required_budget", "field": field}
        trigger_type = str(spec["trigger"].get("type") or "manual").strip()
        if trigger_type not in {"manual", "schedule"}:
            return {"kind": "execution-loop-plan", "status": "blocked", "reason": "unsupported_trigger_type", "supported": ["manual", "schedule"]}
        if trigger_type == "schedule" and not (spec["trigger"].get("every") or spec["trigger"].get("cron")):
            return {"kind": "execution-loop-plan", "status": "blocked", "reason": "missing_schedule_expression"}
        return {"status": "ok"}

    def normalize_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        budget = spec["budget"]
        normalized = dict(spec)
        normalized["id"] = str(spec["id"]).strip()
        normalized["objective"] = " ".join(str(spec["objective"]).split())
        normalized["trigger"] = self.normalize_trigger(spec["trigger"])
        normalized["budget"] = {
            "max_iterations": int(budget["max_iterations"]),
            "max_runtime_seconds": int(budget["max_runtime_seconds"]),
            "max_llm_calls": int(budget.get("max_llm_calls") or 0),
        }
        normalized["side_effects"] = self.normalize_side_effects(spec["side_effects"])
        normalized["steps"] = [self.normalize_step(index, item) for index, item in enumerate(spec["steps"], start=1)]
        normalized["success_when"] = [str(item).strip() for item in spec["success_when"] if str(item).strip()]
        normalized["stop_when"] = [str(item).strip() for item in spec["stop_when"] if str(item).strip()]
        normalized["notify"] = self.normalize_notify(spec.get("notify"))
        normalized["audit"] = spec.get("audit") if isinstance(spec.get("audit"), dict) else {"enabled": True}
        normalized["state"] = spec.get("state") if isinstance(spec.get("state"), dict) else {"backend": "local-json"}
        normalized["target_project"] = str(spec.get("target_project") or "").strip()
        return normalized

    def normalize_trigger(self, trigger: dict[str, Any]) -> dict[str, Any]:
        trigger_type = str(trigger.get("type") or "manual").strip()
        normalized = {"type": trigger_type}
        if trigger.get("every"):
            normalized["every"] = str(trigger["every"]).strip()
        if trigger.get("cron"):
            normalized["cron"] = str(trigger["cron"]).strip()
        return normalized

    def normalize_side_effects(self, side_effects: dict[str, Any]) -> dict[str, Any]:
        external_writes = bool(side_effects.get("external_writes"))
        return {
            "external_writes": external_writes,
            "dry_run_supported": bool(side_effects.get("dry_run_supported", True)),
            "idempotency_key": str(side_effects.get("idempotency_key") or "").strip(),
            "requires_confirmation": bool(side_effects.get("requires_confirmation", external_writes)),
        }

    def normalize_step(self, index: int, item: Any) -> dict[str, Any]:
        if isinstance(item, str):
            step = {"id": f"step-{index}", "type": "capability", "capability": item}
        elif isinstance(item, dict):
            step = dict(item)
            step.setdefault("id", f"step-{index}")
            step.setdefault("type", "capability" if step.get("capability") else "manual")
        else:
            raise ExecutionLoopBuilderError("steps entries must be strings or mappings")
        step["id"] = self.slugify(str(step["id"]))
        step["type"] = str(step["type"]).strip()
        if step.get("capability"):
            step["capability"] = str(step["capability"]).strip()
        if step.get("command"):
            step["command"] = str(step["command"]).strip()
        step["external_writes"] = bool(step.get("external_writes"))
        return step

    def normalize_notify(self, notify: Any) -> dict[str, Any]:
        if not isinstance(notify, dict):
            return {"on": ["failure", "completion"], "channels": ["terminal"], "max_per_run": 2}
        events = notify.get("on") if isinstance(notify.get("on"), list) else ["failure", "completion"]
        channels = notify.get("channels") if isinstance(notify.get("channels"), list) else ["terminal"]
        return {
            "on": [str(item).strip() for item in events if str(item).strip()],
            "channels": [str(item).strip() for item in channels if str(item).strip()],
            "max_per_run": int(notify.get("max_per_run") or 2),
        }

    def review_normalized_spec(self, spec: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        side_effects = spec["side_effects"]
        if not spec["stop_when"]:
            findings.append(self.finding("critical", "missing_stop_condition", "Loop has no stop_when.", "Loop can run indefinitely.", "Define at least one stop condition."))
        if spec["budget"]["max_iterations"] > 50:
            findings.append(self.finding("medium", "high_iteration_budget", "max_iterations is high.", "Loop can consume excessive time or tokens.", "Use the smallest useful iteration budget."))
        if spec["budget"]["max_runtime_seconds"] > 3600:
            findings.append(self.finding("medium", "high_runtime_budget", "max_runtime_seconds is above one hour.", "Long local loops are hard to audit.", "Split into smaller scheduled runs."))
        if spec["budget"]["max_llm_calls"] > spec["budget"]["max_iterations"]:
            findings.append(self.finding("medium", "llm_budget_exceeds_iterations", "max_llm_calls exceeds max_iterations.", "LLM calls can dominate cost.", "Limit LLM calls to review/classification steps only."))
        if side_effects["external_writes"] and not side_effects["dry_run_supported"]:
            findings.append(self.finding("critical", "external_write_without_dry_run", "external_writes=true without dry_run_supported.", "Repeated writes can duplicate effects.", "Require dry-run before any real write."))
        if side_effects["external_writes"] and not side_effects["idempotency_key"]:
            findings.append(self.finding("high", "external_write_without_idempotency", "external_writes=true without idempotency_key.", "Retries can duplicate writes.", "Define an idempotency key or state check."))
        for step in spec["steps"]:
            capability = step.get("capability")
            if capability and not CAPABILITY_REF_PATTERN.fullmatch(str(capability)):
                findings.append(self.finding("high", "invalid_capability_reference", f"Invalid capability reference: {capability}", "Loop cannot route the step reliably.", "Use agent-id.capability-id."))
            if step.get("command") and DESTRUCTIVE_PATTERN.search(str(step["command"])):
                findings.append(self.finding("critical", "destructive_step", f"Destructive command marker in step {step['id']}.", "Loop can repeat destructive work.", "Remove destructive command or require a separate confirmed operator."))
            if step.get("external_writes") and not side_effects["external_writes"]:
                findings.append(self.finding("high", "step_write_not_declared_globally", f"Step {step['id']} declares external writes but loop does not.", "Scheduler permission checks can be bypassed by inaccurate metadata.", "Set side_effects.external_writes=true."))
        if "iteration" in spec["notify"]["on"] and spec["notify"]["max_per_run"] > 3:
            findings.append(self.finding("medium", "notification_spam_risk", "Notifications include every iteration with high max_per_run.", "Loop can spam operators.", "Notify on failure/completion or cap notifications tightly."))
        return findings

    def review_text(self, text: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lower = text.lower()
        if "max_iterations" not in lower:
            findings.append(self.finding("critical", "missing_max_iterations", "Text does not mention max_iterations.", "Loop may run indefinitely.", "Declare max_iterations."))
        if "max_runtime_seconds" not in lower:
            findings.append(self.finding("critical", "missing_max_runtime_seconds", "Text does not mention max_runtime_seconds.", "Loop may run too long.", "Declare max_runtime_seconds."))
        if "stop_when" not in lower:
            findings.append(self.finding("critical", "missing_stop_when", "Text does not mention stop_when.", "Loop may lack a stop criterion.", "Declare stop_when."))
        if DESTRUCTIVE_PATTERN.search(text):
            findings.append(self.finding("critical", "destructive_step", "Destructive marker appears in loop text.", "Loop can repeat destructive work.", "Move destructive action to confirmed operator."))
        if SECRET_PATTERN.search(text):
            findings.append(self.finding("critical", "secret_marker_in_loop", "Secret assignment marker appears in loop text.", "Secrets can leak into artifacts.", "Use env references or provider configuration."))
        return findings

    def findings_from_validation(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        if result.get("status") == "needs-input":
            return [
                self.finding("critical", f"missing_{field}", f"Missing required field: {field}.", "Loop contract is incomplete.", "Provide the required field.")
                for field in result.get("missing_fields", [])
            ]
        reason = str(result.get("reason") or "invalid_loop_contract")
        return [self.finding("critical", reason, reason, "Loop contract is invalid.", "Fix the loop spec.")]

    def build_loop_files(self, spec: dict[str, Any]) -> list[tuple[str, str]]:
        prefix = f"{spec['id']}/"
        return [
            (f"{prefix}loop-spec.normalized.json", json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n"),
            (f"{prefix}loop_runner.py", self.render_loop_runner(spec)),
            (f"{prefix}README.md", self.render_loop_readme(spec)),
            (f"{prefix}tests/test_loop_runner.py", self.render_loop_test(spec)),
        ]

    def render_loop_runner(self, spec: dict[str, Any]) -> str:
        spec_json = json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True)
        spec_literal = json.dumps(spec_json)
        body = f'''\
#!/usr/bin/env python3
"""Generated controlled execution loop runner for {spec["id"]}."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path


LOOP_SPEC = json.loads({spec_literal})


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state(path: Path) -> dict:
    if not path.exists():
        return {{"runs": []}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\\n", encoding="utf-8")


def run_loop(*, state_dir: Path, execute: bool, yes: bool) -> dict:
    budget = LOOP_SPEC["budget"]
    side_effects = LOOP_SPEC["side_effects"]
    if execute and side_effects.get("external_writes") and not yes:
        return {{"status": "blocked", "reason": "external writes require --yes", "exit_code": 2}}
    state_path = state_dir / f"{{LOOP_SPEC['id']}}.state.json"
    state = load_state(state_path)
    started = time.monotonic()
    run = {{"id": now_iso(), "status": "running", "iterations": [], "stop_reason": None}}
    for iteration in range(1, int(budget["max_iterations"]) + 1):
        if time.monotonic() - started >= int(budget["max_runtime_seconds"]):
            run["stop_reason"] = "max_runtime_seconds_reached"
            break
        observed_steps = []
        for step in LOOP_SPEC["steps"]:
            observed_steps.append({{
                "step_id": step.get("id"),
                "type": step.get("type"),
                "capability": step.get("capability"),
                "status": "planned" if not execute else "skipped_mvp",
            }})
        run["iterations"].append({{"iteration": iteration, "steps": observed_steps, "at": now_iso()}})
        if not execute:
            run["stop_reason"] = "dry_run"
            break
    if run["stop_reason"] is None:
        run["stop_reason"] = "max_iterations_reached"
    run["status"] = "completed"
    state.setdefault("runs", []).append(run)
    state["last_run"] = run
    save_state(state_path, state)
    return {{"status": "ok", "loop_id": LOOP_SPEC["id"], "state_path": str(state_path), "run": run}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run generated execution loop")
    parser.add_argument("--state-dir", default=".agent-devkit-loop-state")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    result = run_loop(state_dir=Path(args.state_dir), execute=args.execute, yes=args.yes)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result.get("exit_code") or 0)


if __name__ == "__main__":
    raise SystemExit(main())
'''
        return body

    def render_loop_readme(self, spec: dict[str, Any]) -> str:
        return "\n".join([
            f"# Execution Loop: {spec['id']}",
            "",
            spec["objective"],
            "",
            "## Dry Run",
            "",
            "```sh",
            "python loop_runner.py --state-dir .agent-devkit-loop-state",
            "```",
            "",
            "## Execute",
            "",
            "```sh",
            "python loop_runner.py --execute --state-dir .agent-devkit-loop-state",
            "```",
            "",
            "External writes are not granted automatically. Review the spec, state and audit output before enabling real side effects.",
            "",
        ])

    def render_loop_test(self, _spec: dict[str, Any]) -> str:
        return "\n".join([
            "import json",
            "import subprocess",
            "import sys",
            "from pathlib import Path",
            "",
            "",
            "def test_loop_runner_dry_run(tmp_path):",
            "    runner = Path(__file__).resolve().parents[1] / 'loop_runner.py'",
            "    result = subprocess.run([sys.executable, str(runner), '--state-dir', str(tmp_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)",
            "    assert result.returncode == 0, result.stderr",
            "    payload = json.loads(result.stdout)",
            "    assert payload['status'] == 'ok'",
            "    assert payload['run']['stop_reason'] == 'dry_run'",
            "",
        ])

    def scheduler_task_payload(self, spec: dict[str, Any]) -> dict[str, Any]:
        return {
            "task_id": spec["id"],
            "title": f"Execution loop: {spec['id']}",
            "prompt": spec["objective"],
            "schedule": self.scheduler_schedule(spec["trigger"]),
            "action": {
                "type": "loop-runner",
                "loop_id": spec["id"],
                "agent": "execution-loop-builder",
                "capability": "generate-loop-runner",
                "external_writes": bool(spec["side_effects"]["external_writes"]),
            },
            "permissions": {"mode": "report-only"},
            "notifications": [{"type": "terminal", "on": spec["notify"]["on"]}],
            "enabled": spec["trigger"]["type"] != "manual",
        }

    def scheduler_schedule(self, trigger: dict[str, Any]) -> dict[str, Any]:
        if trigger["type"] != "schedule":
            return {"type": "manual"}
        if trigger.get("every"):
            return {"type": "interval", "every": trigger["every"]}
        return {"type": "cron", "cron": trigger.get("cron")}

    def write_or_plan_files(
        self,
        *,
        kind: str,
        files: list[tuple[str, str]],
        target_root: Path,
        execute: bool,
        allow_overwrite: bool,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        if not target_root.exists() or not target_root.is_dir():
            return {"kind": kind, "status": "blocked", "reason": "target_project_missing", "target_project": str(target_root)}
        checked_files = []
        for relative_path, content in files:
            target = (target_root / relative_path).resolve()
            if Path(relative_path).is_absolute() or not self.is_inside(target_root, target):
                return {"kind": kind, "status": "blocked", "reason": "path_outside_target_project", "path": relative_path}
            checked_files.append((relative_path, target, content))
        if not execute:
            return {
                "kind": kind,
                "status": "planned",
                "dry_run": True,
                "target_project": str(target_root),
                "planned_files": [
                    {"path": relative_path, "absolute_path": str(target), "bytes": len(content.encode("utf-8"))}
                    for relative_path, target, content in checked_files
                ],
                **extra,
                "next_steps": ["Rerun with --execute after reviewing the planned files."],
            }
        existing = [target for _relative_path, target, _content in checked_files if target.exists()]
        if existing and not allow_overwrite:
            return {
                "kind": kind,
                "status": "blocked",
                "reason": "target_exists",
                "target_project": str(target_root),
                "existing_files": [str(path) for path in existing],
                **extra,
            }
        written_files = []
        for _relative_path, target, content in checked_files:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written_files.append({"path": str(target), "bytes": len(content.encode("utf-8"))})
        return {"kind": kind, "status": "written", "dry_run": False, "target_project": str(target_root), "written_files": written_files, **extra}

    def loop_summary(self, spec: dict[str, Any] | None) -> dict[str, Any]:
        if spec is None:
            return {}
        return {
            "id": spec["id"],
            "objective": spec["objective"],
            "trigger": spec["trigger"],
            "max_iterations": spec["budget"]["max_iterations"],
            "max_runtime_seconds": spec["budget"]["max_runtime_seconds"],
            "external_writes": spec["side_effects"]["external_writes"],
            "steps": len(spec["steps"]),
        }

    def public_file_plan(self, files: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return [{"path": path, "bytes": len(content.encode("utf-8"))} for path, content in files]

    def open_questions(self, spec: dict[str, Any]) -> list[str]:
        questions = []
        if not spec["success_when"]:
            questions.append("Qual evidencia objetiva indica sucesso?")
        if spec["side_effects"]["external_writes"] and not spec["side_effects"]["idempotency_key"]:
            questions.append("Qual chave de idempotencia evita duplicar escrita externa?")
        if spec["trigger"]["type"] == "manual":
            questions.append("O loop deve permanecer manual ou ser registrado em schedule?")
        return questions

    def question_for_missing_field(self, field: str) -> str:
        return {
            "id": "Qual identificador kebab-case do loop?",
            "objective": "Qual objetivo operacional do loop?",
            "trigger": "O loop e manual ou schedule?",
            "budget": "Quais limites de iteracao, tempo e chamadas LLM?",
            "side_effects": "O loop realiza escrita externa?",
            "steps": "Quais steps/capabilities compoem cada iteracao?",
            "success_when": "Quais criterios indicam sucesso?",
            "stop_when": "Quais criterios interrompem o loop?",
        }.get(field, f"Informe o campo {field}.")

    def positive_int(self, value: Any) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    def finding(self, severity: str, code: str, evidence: str, risk: str, recommendation: str) -> dict[str, Any]:
        return {
            "severity": severity,
            "code": code,
            "evidence": self.redact_text(evidence),
            "risk": risk,
            "recommendation": recommendation,
        }

    def redact_text(self, text: str) -> str:
        return SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=<redacted>", text)

    def dedupe_findings(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[Any, ...]] = set()
        unique = []
        for finding in findings:
            key = (finding.get("code"), finding.get("evidence"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(finding)
        return unique

    def slugify(self, value: str) -> str:
        slug = SLUG_PATTERN.sub("-", value.lower()).strip("-")
        return slug or "step"

    def is_inside(self, root: Path, target: Path) -> bool:
        try:
            target.relative_to(root.resolve())
            return True
        except ValueError:
            return False
