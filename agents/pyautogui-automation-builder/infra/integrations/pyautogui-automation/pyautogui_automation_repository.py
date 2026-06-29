"""Repository for deterministic PyAutoGUI desktop automation generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


REQUIRED_SPEC_FIELDS = (
    "automation_name",
    "purpose",
    "target_app",
    "target_window",
    "platform",
    "steps",
    "screen_preconditions",
    "verification_strategy",
    "safer_alternatives_checked",
    "user_accepts_visual_risk",
    "side_effects",
    "coordinates_policy",
)
PLATFORMS = {"macos", "windows", "linux", "cross-platform"}
SIDE_EFFECTS = {"read-only", "navigation", "data-entry", "external-write", "destructive"}
COORDINATES_POLICIES = {"relative", "image-recognition", "window-relative", "absolute-last-resort"}
SAFER_ALTERNATIVES = {
    "api",
    "cli",
    "mcp",
    "playwright",
    "selenium",
    "applescript",
    "windows-ui-automation",
}
UNAVAILABLE_MARKERS = {"none", "not-available", "unavailable", "checked-none-available"}
FORBIDDEN_MARKER_PATTERN = re.compile(r"\b(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)\b\s*[:=]")
COORDINATE_CALL_PATTERN = re.compile(r"\b(?:click|moveTo|dragTo)\s*\(\s*\d+\s*,\s*\d+")
KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class PyAutoGUIAutomationError(RuntimeError):
    """Raised when the builder cannot read or process an input spec."""


class PyAutoGUIAutomationRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[5]

    def plan_desktop_automation(self, *, spec_path: Path) -> dict[str, Any]:
        spec = self.load_spec(spec_path)
        spec_result = self.validate_spec(spec)
        if spec_result["status"] != "ok":
            return spec_result

        normalized = self.normalize_spec(spec)
        blocked = self.detect_forbidden_content(normalized)
        if blocked:
            return blocked

        alternative_result = self.validate_safer_alternatives(normalized["safer_alternatives_checked"])
        if alternative_result["status"] != "ok":
            return alternative_result

        risk_result = self.validate_visual_risk(normalized)
        if risk_result["status"] != "ok":
            return risk_result

        files = self.build_pyautogui_files(normalized)
        return {
            "kind": "desktop-automation-plan",
            "status": "ok",
            "automation": self.automation_summary(normalized),
            "platform": normalized["platform"],
            "side_effects": normalized["side_effects"],
            "coordinates_policy": normalized["coordinates_policy"],
            "write_policy": "read_only",
            "planned_artifacts": self.public_file_plan(files),
            "guardrails": self.side_effect_guardrails(normalized["side_effects"]),
            "questions": self.open_questions(normalized),
        }

    def generate_pyautogui_script(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_desktop_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        content = self.render_pyautogui_script(spec)
        return {
            "kind": "pyautogui-script",
            "status": "ok",
            "automation": self.automation_summary(spec),
            "artifact": "pyautogui_automation.py",
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "write_policy": "output_only",
        }

    def generate_pyautogui_project_files(
        self,
        *,
        spec_path: Path,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_desktop_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "pyautogui-project-files",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }

        target_root = Path(str(target_project)).expanduser().resolve()
        files = self.build_pyautogui_files(spec, base_dir=spec["automation_slug"])
        return self.write_or_plan_files(
            kind="pyautogui-project-files",
            files=files,
            target_root=target_root,
            execute=execute,
            allow_overwrite=allow_overwrite,
            extra={"automation": self.automation_summary(spec), "side_effects": spec["side_effects"]},
        )

    def review_pyautogui_script(self, *, text: str, side_effects: str = "navigation") -> dict[str, Any]:
        normalized_side_effects = str(side_effects or "navigation").strip()
        findings: list[str] = []
        if not text.strip():
            findings.append("pyautogui script is empty")
        lower_text = text.lower()
        if "pyautogui.failsafe = true" not in lower_text and ".failsafe = true" not in lower_text:
            findings.append("pyautogui script must set pyautogui.FAILSAFE = True")
        for flag in ("--dry-run", "--execute", "--confirm", "--screenshot-dir", "--timeout", "--abort-file"):
            if flag not in text:
                findings.append(f"pyautogui script must expose {flag}")
        if "screenshot" not in lower_text:
            findings.append("pyautogui script must capture screenshots")
        if "before.png" not in lower_text or "after.png" not in lower_text or "error.png" not in lower_text:
            findings.append("pyautogui script should capture before, after and error screenshots")
        if "target_window" not in lower_text and "--target-window" not in text:
            findings.append("pyautogui script should validate target window or expose --target-window")
        if normalized_side_effects != "read-only" and "--confirm" not in text:
            findings.append("pyautogui script with side effects must require --confirm")
        if "return 0" not in text and "sys.exit(0)" not in text:
            findings.append("pyautogui script should return a predictable success exit code")
        if self.detect_text_forbidden_content(text):
            findings.append("pyautogui script contains a secret marker")
        if COORDINATE_CALL_PATTERN.search(text) and "--region" not in text and "region" not in lower_text:
            findings.append("absolute coordinates require region/window-relative guardrails")

        valid = not findings
        return {
            "kind": "pyautogui-review",
            "status": "ok" if valid else "failed",
            "valid": valid,
            "side_effects": normalized_side_effects,
            "findings": findings,
            "write_policy": "read_only",
        }

    def wrap_pyautogui_as_capability(
        self,
        *,
        spec_path: Path,
        agent_id: str,
        capability_id: str,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_desktop_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        if not KEBAB_CASE.match(agent_id):
            return {
                "kind": "pyautogui-capability-wrapper",
                "status": "blocked",
                "reason": "invalid_agent_id",
                "risks": ["agent-id must be kebab-case."],
            }
        if not KEBAB_CASE.match(capability_id):
            return {
                "kind": "pyautogui-capability-wrapper",
                "status": "blocked",
                "reason": "invalid_capability_id",
                "risks": ["capability-id must be kebab-case."],
            }

        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "pyautogui-capability-wrapper",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }

        target_root = Path(str(target_project)).expanduser().resolve()
        files = self.build_capability_wrapper_files(spec, agent_id=agent_id, capability_id=capability_id)
        return self.write_or_plan_files(
            kind="pyautogui-capability-wrapper",
            files=files,
            target_root=target_root,
            execute=execute,
            allow_overwrite=allow_overwrite,
            extra={
                "agent_id": agent_id,
                "capability_id": capability_id,
                "capability_write_policy": self.capability_write_policy(spec["side_effects"]),
            },
        )

    def load_spec(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise PyAutoGUIAutomationError(f"spec not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            payload = json.loads(text)
        else:
            payload = yaml.safe_load(text) or {}
        if not isinstance(payload, dict):
            raise PyAutoGUIAutomationError("spec must be a mapping")
        return payload

    def validate_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        missing = [
            field
            for field in REQUIRED_SPEC_FIELDS
            if field not in spec or spec.get(field) is None or spec.get(field) == ""
        ]
        if missing:
            return {
                "kind": "desktop-automation-plan",
                "status": "needs-input",
                "missing_fields": missing,
                "questions": [self.question_for_missing_field(field) for field in missing],
            }
        for field in ("steps", "screen_preconditions", "quality_gates", "safer_alternatives_checked"):
            if spec.get(field) is not None and not isinstance(spec[field], list):
                return {
                    "kind": "desktop-automation-plan",
                    "status": "blocked",
                    "reason": "invalid_list_field",
                    "field": field,
                    "risks": [f"{field} must be a list when provided."],
                }
        platform = str(spec.get("platform") or "").strip().lower()
        if platform not in PLATFORMS:
            return {
                "kind": "desktop-automation-plan",
                "status": "blocked",
                "reason": "unsupported_platform",
                "supported_values": sorted(PLATFORMS),
            }
        side_effects = str(spec.get("side_effects") or "").strip()
        if side_effects not in SIDE_EFFECTS:
            return {
                "kind": "desktop-automation-plan",
                "status": "blocked",
                "reason": "invalid_side_effects",
                "supported_values": sorted(SIDE_EFFECTS),
            }
        coordinates_policy = str(spec.get("coordinates_policy") or "").strip()
        if coordinates_policy not in COORDINATES_POLICIES:
            return {
                "kind": "desktop-automation-plan",
                "status": "blocked",
                "reason": "invalid_coordinates_policy",
                "supported_values": sorted(COORDINATES_POLICIES),
            }
        return {"status": "ok"}

    def normalize_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(spec)
        normalized["automation_name"] = " ".join(str(spec["automation_name"]).split())
        normalized["automation_slug"] = self.slugify(normalized["automation_name"])
        normalized["purpose"] = " ".join(str(spec["purpose"]).split())
        normalized["target_app"] = " ".join(str(spec["target_app"]).split())
        normalized["target_window"] = " ".join(str(spec["target_window"]).split())
        normalized["platform"] = str(spec["platform"]).strip().lower()
        normalized["side_effects"] = str(spec["side_effects"]).strip()
        normalized["coordinates_policy"] = str(spec["coordinates_policy"]).strip()
        normalized["steps"] = [str(item).strip() for item in spec.get("steps") or []]
        normalized["screen_preconditions"] = [str(item).strip() for item in spec.get("screen_preconditions") or []]
        normalized["quality_gates"] = [str(item).strip() for item in spec.get("quality_gates") or []]
        normalized["safer_alternatives_checked"] = [
            str(item).strip().lower() for item in spec.get("safer_alternatives_checked") or []
        ]
        normalized["verification_strategy"] = " ".join(str(spec["verification_strategy"]).split())
        normalized["user_accepts_visual_risk"] = self.as_bool(spec["user_accepts_visual_risk"])
        normalized["absolute_coordinate_justification"] = " ".join(
            str(spec.get("absolute_coordinate_justification") or "").split()
        )
        if spec.get("target_project"):
            normalized["target_project"] = str(spec["target_project"]).strip()
        return normalized

    def validate_safer_alternatives(self, checked: list[str]) -> dict[str, Any]:
        if not checked:
            return {
                "kind": "desktop-automation-plan",
                "status": "needs-safer-alternative-review",
                "reason": "safer_alternatives_not_checked",
                "risks": ["PyAutoGUI cannot be selected before safer alternatives are reviewed."],
                "next_steps": ["Check API, CLI, MCP, browser automation and native OS automation first."],
            }
        available = sorted({item for item in checked if item in SAFER_ALTERNATIVES})
        if available:
            return {
                "kind": "desktop-automation-plan",
                "status": "needs-safer-alternative-review",
                "reason": "safer_alternative_available",
                "available_alternatives": available,
                "risks": ["PyAutoGUI should not be used while a safer automation path is available."],
            }
        unknown = sorted({item for item in checked if item not in UNAVAILABLE_MARKERS})
        if unknown:
            return {
                "kind": "desktop-automation-plan",
                "status": "blocked",
                "reason": "unsupported_safer_alternative_marker",
                "unsupported_values": unknown,
                "supported_unavailable_markers": sorted(UNAVAILABLE_MARKERS),
            }
        return {"status": "ok"}

    def validate_visual_risk(self, spec: dict[str, Any]) -> dict[str, Any]:
        if not spec["user_accepts_visual_risk"]:
            return {
                "kind": "desktop-automation-plan",
                "status": "needs-input",
                "missing_fields": ["user_accepts_visual_risk"],
                "questions": ["O usuario aceita explicitamente o risco de automacao visual PyAutoGUI?"],
            }
        if spec["side_effects"] == "destructive":
            return {
                "kind": "desktop-automation-plan",
                "status": "blocked",
                "reason": "destructive_desktop_automation_blocked",
                "risks": ["Destructive desktop automation is blocked by default for PyAutoGUI."],
            }
        if spec["coordinates_policy"] == "absolute-last-resort" and not spec["absolute_coordinate_justification"]:
            return {
                "kind": "desktop-automation-plan",
                "status": "blocked",
                "reason": "absolute_coordinates_need_justification",
                "risks": ["Absolute coordinates require a last-resort justification and region guardrails."],
            }
        return {"status": "ok"}

    def detect_forbidden_content(self, spec: dict[str, Any]) -> dict[str, Any] | None:
        for _key, value in self.iter_key_values(spec):
            if isinstance(value, str) and self.detect_text_forbidden_content(value):
                return {
                    "kind": "desktop-automation-plan",
                    "status": "blocked",
                    "reason": "forbidden_sensitive_marker",
                    "risks": ["Spec contains text that looks like a hardcoded secret."],
                }
        return None

    def detect_text_forbidden_content(self, value: str) -> bool:
        return bool(FORBIDDEN_MARKER_PATTERN.search(value))

    def build_pyautogui_files(self, spec: dict[str, Any], *, base_dir: str = "") -> list[tuple[str, str]]:
        prefix = f"{base_dir}/" if base_dir else ""
        return [
            (f"{prefix}pyautogui_automation.py", self.render_pyautogui_script(spec)),
            (f"{prefix}README.md", self.render_readme(spec)),
            (f"{prefix}requirements.txt", "pyautogui>=0.9.54\n"),
            (f"{prefix}tests/test_pyautogui_automation.py", self.render_pyautogui_test(spec)),
        ]

    def build_capability_wrapper_files(
        self,
        spec: dict[str, Any],
        *,
        agent_id: str,
        capability_id: str,
    ) -> list[tuple[str, str]]:
        base = f"agents/{agent_id}/capabilities/{capability_id}"
        return [
            (f"{base}/capability.yaml", self.render_capability_yaml(spec, agent_id=agent_id, capability_id=capability_id)),
            (f"{base}/workflow.md", self.render_capability_workflow(spec, capability_id=capability_id)),
            (f"{base}/decision-rules.md", self.render_capability_decision_rules(spec)),
            (f"{base}/runner.py", self.render_pyautogui_script(spec)),
        ]

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
            return {
                "kind": kind,
                "status": "blocked",
                "reason": "target_project_missing",
                "target_project": str(target_root),
                "risks": ["target_project must exist before files can be written."],
            }

        checked_files = []
        for relative_path, content in files:
            target = (target_root / relative_path).resolve()
            if Path(relative_path).is_absolute() or not self.is_inside(target_root, target):
                return {
                    "kind": kind,
                    "status": "blocked",
                    "reason": "path_outside_target_project",
                    "path": relative_path,
                    "target_project": str(target_root),
                }
            checked_files.append((relative_path, target, content))

        if not execute:
            return {
                "kind": kind,
                "status": "planned",
                "dry_run": True,
                "target_project": str(target_root),
                "planned_files": [
                    {
                        "path": relative_path,
                        "absolute_path": str(target),
                        "bytes": len(content.encode("utf-8")),
                    }
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
                "next_steps": ["Rerun with --allow-overwrite only after reviewing existing files."],
            }

        written_files = []
        for _relative_path, target, content in checked_files:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written_files.append({"path": str(target), "bytes": len(content.encode("utf-8"))})

        return {
            "kind": kind,
            "status": "written",
            "dry_run": False,
            "target_project": str(target_root),
            "written_files": written_files,
            **extra,
        }

    def render_pyautogui_script(self, spec: dict[str, Any]) -> str:
        confirmation_block = [
            "    if args.execute and not args.confirm:",
            "        logger.error(\"real PyAutoGUI actions require --confirm after reviewing --dry-run output\")",
            "        return 2",
        ]
        return "\n".join(
            [
                "#!/usr/bin/env python3",
                f'"""PyAutoGUI desktop automation: {spec["automation_name"]}."""',
                "",
                "from __future__ import annotations",
                "",
                "import argparse",
                "import json",
                "import logging",
                "import time",
                "from pathlib import Path",
                "",
                f"TARGET_APP = {spec['target_app']!r}",
                f"TARGET_WINDOW = {spec['target_window']!r}",
                f"STEPS = {spec['steps']!r}",
                f"SCREEN_PRECONDITIONS = {spec['screen_preconditions']!r}",
                f"VERIFICATION_STRATEGY = {spec['verification_strategy']!r}",
                f"SIDE_EFFECTS = {spec['side_effects']!r}",
                f"COORDINATES_POLICY = {spec['coordinates_policy']!r}",
                "",
                "",
                "def build_parser() -> argparse.ArgumentParser:",
                f"    parser = argparse.ArgumentParser(description={spec['purpose']!r})",
                "    parser.add_argument(\"--dry-run\", action=\"store_true\", help=\"show planned desktop actions without touching UI\")",
                "    parser.add_argument(\"--execute\", action=\"store_true\", help=\"run real PyAutoGUI actions\")",
                "    parser.add_argument(\"--confirm\", action=\"store_true\", help=\"confirm real UI side effects after dry-run review\")",
                "    parser.add_argument(\"--screenshot-dir\", default=\"pyautogui-artifacts\")",
                "    parser.add_argument(\"--target-window\", default=TARGET_WINDOW)",
                "    parser.add_argument(\"--pause\", type=float, default=0.2)",
                "    parser.add_argument(\"--timeout\", type=int, default=20)",
                "    parser.add_argument(\"--abort-file\", default=\"ABORT_PYAUTOGUI\")",
                "    parser.add_argument(\"--region\", help=\"optional x,y,width,height region guardrail\")",
                "    return parser",
                "",
                "",
                "def pyautogui_import():",
                "    import pyautogui",
                "    pyautogui.FAILSAFE = True",
                "    return pyautogui",
                "",
                "",
                "def planned_actions(args: argparse.Namespace) -> dict:",
                "    return {",
                f"        \"automation\": {spec['automation_slug']!r},",
                "        \"target_app\": TARGET_APP,",
                "        \"target_window\": args.target_window,",
                "        \"side_effects\": SIDE_EFFECTS,",
                "        \"coordinates_policy\": COORDINATES_POLICY,",
                "        \"screen_preconditions\": SCREEN_PRECONDITIONS,",
                "        \"verification_strategy\": VERIFICATION_STRATEGY,",
                "        \"steps\": STEPS,",
                "    }",
                "",
                "",
                "def ensure_abort_not_requested(args: argparse.Namespace) -> None:",
                "    abort_path = Path(args.abort_file)",
                "    if abort_path.exists():",
                "        raise RuntimeError(f\"abort file exists: {abort_path}\")",
                "",
                "",
                "def capture_screenshot(pyautogui, screenshot_dir: Path, name: str, region: tuple[int, int, int, int] | None) -> str:",
                "    screenshot_dir.mkdir(parents=True, exist_ok=True)",
                "    path = screenshot_dir / name",
                "    image = pyautogui.screenshot(region=region)",
                "    image.save(path)",
                "    return str(path)",
                "",
                "",
                "def parse_region(value: str | None) -> tuple[int, int, int, int] | None:",
                "    if not value:",
                "        return None",
                "    parts = [int(part.strip()) for part in value.split(\",\")]",
                "    if len(parts) != 4:",
                "        raise ValueError(\"--region must be x,y,width,height\")",
                "    return tuple(parts)",
                "",
                "",
                "def validate_target_window(pyautogui, expected: str) -> dict:",
                "    if not expected:",
                "        return {\"status\": \"warning\", \"reason\": \"target_window_not_provided\"}",
                "    get_active_window = getattr(pyautogui, \"getActiveWindow\", None)",
                "    if get_active_window is None:",
                "        return {\"status\": \"warning\", \"reason\": \"active_window_check_unavailable\"}",
                "    active = get_active_window()",
                "    title = getattr(active, \"title\", \"\") if active else \"\"",
                "    if expected.lower() not in title.lower():",
                "        raise RuntimeError(f\"active window mismatch: expected {expected!r}, got {title!r}\")",
                "    return {\"status\": \"ok\", \"active_window\": title}",
                "",
                "",
                "def run_desktop(args: argparse.Namespace) -> dict:",
                "    pyautogui = pyautogui_import()",
                "    pyautogui.PAUSE = args.pause",
                "    screenshot_dir = Path(args.screenshot_dir)",
                "    region = parse_region(args.region)",
                "    started_at = time.monotonic()",
                "    result = {\"status\": \"ok\", \"screenshots\": {}, \"steps\": []}",
                "    try:",
                "        ensure_abort_not_requested(args)",
                "        result[\"window_check\"] = validate_target_window(pyautogui, args.target_window)",
                "        result[\"screenshots\"][\"before\"] = capture_screenshot(pyautogui, screenshot_dir, \"before.png\", region)",
                "        for index, step in enumerate(STEPS, start=1):",
                "            ensure_abort_not_requested(args)",
                "            if time.monotonic() - started_at > args.timeout:",
                "                raise TimeoutError(\"PyAutoGUI automation timed out\")",
                "            result[\"steps\"].append({\"index\": index, \"description\": step, \"status\": \"manual-review-required\"})",
                "        result[\"screenshots\"][\"after\"] = capture_screenshot(pyautogui, screenshot_dir, \"after.png\", region)",
                "        return result",
                "    except Exception as exc:",
                "        try:",
                "            result[\"screenshots\"][\"error\"] = capture_screenshot(pyautogui, screenshot_dir, \"error.png\", region)",
                "        except Exception as screenshot_exc:",
                "            result[\"screenshot_error\"] = str(screenshot_exc)",
                "        result[\"status\"] = \"failed\"",
                "        result[\"error\"] = str(exc)",
                "        return result",
                "",
                "",
                "def main(argv: list[str] | None = None) -> int:",
                "    parser = build_parser()",
                "    args = parser.parse_args(argv)",
                "    logging.basicConfig(level=logging.INFO, format=\"%(levelname)s %(message)s\")",
                "    logger = logging.getLogger(\"pyautogui-automation\")",
                "    if args.execute and args.dry_run:",
                "        logger.error(\"choose either --dry-run or --execute\")",
                "        return 2",
                *confirmation_block,
                "    if not args.execute:",
                "        print(json.dumps({\"dry_run\": True, \"plan\": planned_actions(args)}, indent=2))",
                "        return 0",
                "    result = run_desktop(args)",
                "    print(json.dumps(result, indent=2))",
                "    return 0 if result.get(\"status\") == \"ok\" else 1",
                "",
                "",
                "if __name__ == \"__main__\":",
                "    raise SystemExit(main())",
                "",
            ]
        )

    def render_readme(self, spec: dict[str, Any]) -> str:
        steps = self.markdown_list(spec["steps"], fallback="No steps.")
        preconditions = self.markdown_list(spec["screen_preconditions"], fallback="No screen preconditions.")
        gates = self.markdown_list(spec["quality_gates"], fallback="Review dry-run, target window and screenshots.")
        alternatives = self.markdown_list(
            spec["safer_alternatives_checked"],
            fallback="No safer alternatives were recorded.",
        )
        return "\n".join(
            [
                f"# {spec['automation_name']}",
                "",
                spec["purpose"],
                "",
                "## Target",
                "",
                f"- App: `{spec['target_app']}`",
                f"- Window: `{spec['target_window']}`",
                f"- Platform: `{spec['platform']}`",
                "",
                "## Usage",
                "",
                "```bash",
                "python pyautogui_automation.py --dry-run",
                "python pyautogui_automation.py --execute --confirm --screenshot-dir artifacts",
                "```",
                "",
                "## Steps",
                "",
                steps,
                "",
                "## Screen Preconditions",
                "",
                preconditions,
                "",
                "## Verification",
                "",
                spec["verification_strategy"],
                "",
                "## Safer Alternatives Checked",
                "",
                alternatives,
                "",
                "## Quality Gates",
                "",
                gates,
                "",
                "## Guardrails",
                "",
                "- PyAutoGUI is a last-resort path.",
                "- Real UI actions require `--execute --confirm`.",
                "- `pyautogui.FAILSAFE = True` is enabled.",
                "- Screenshots are captured before, after and on error.",
                "- Do not hardcode credentials or secrets.",
                "",
            ]
        )

    def render_pyautogui_test(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "import json",
                "import subprocess",
                "import sys",
                "from pathlib import Path",
                "",
                "",
                "def test_pyautogui_automation_dry_run_returns_plan_without_pyautogui():",
                "    script = Path(__file__).resolve().parents[1] / \"pyautogui_automation.py\"",
                "    result = subprocess.run(",
                "        [sys.executable, str(script), \"--dry-run\"],",
                "        text=True,",
                "        capture_output=True,",
                "        check=False,",
                "    )",
                "    assert result.returncode == 0, result.stderr",
                "    payload = json.loads(result.stdout)",
                "    assert payload[\"dry_run\"] is True",
                f"    assert payload[\"plan\"][\"automation\"] == {spec['automation_slug']!r}",
                "",
            ]
        )

    def render_capability_yaml(self, spec: dict[str, Any], *, agent_id: str, capability_id: str) -> str:
        payload = {
            "id": f"{agent_id}.{capability_id}",
            "kind": "capability",
            "name": self.title_from_id(capability_id),
            "version": "0.1.0",
            "status": "draft",
            "purpose": spec["purpose"],
            "entrypoint": {"runner": "runner.py", "workflow": "workflow.md"},
            "inputs": {
                "required": [],
                "optional": [
                    "dry-run",
                    "execute",
                    "confirm",
                    "screenshot-dir",
                    "target-window",
                    "pause",
                    "timeout",
                    "abort-file",
                    "region",
                ],
            },
            "outputs": {"artifacts": ["pyautogui-result.json", "before.png", "after.png", "error.png"]},
            "write_policy": self.capability_write_policy(spec["side_effects"]),
        }
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)

    def render_capability_workflow(self, spec: dict[str, Any], *, capability_id: str) -> str:
        return "\n".join(
            [
                "# Workflow",
                "",
                f"1. Executar `{capability_id}` em dry-run por padrao.",
                "2. Revisar janela alvo, regiao, pre-condicoes e screenshots esperados.",
                "3. Executar com `--execute --confirm` apenas apos revisao humana.",
                "4. Interromper criando o arquivo de abort configurado por `--abort-file`.",
                "5. Retornar JSON e screenshots antes/depois/erro.",
                "",
            ]
        )

    def render_capability_decision_rules(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "# Decision Rules",
                "",
                f"- Side effects classificados como `{spec['side_effects']}`.",
                "- PyAutoGUI e ultimo recurso; preferir API, CLI, MCP ou automacao nativa quando disponivel.",
                "- Escrita real exige confirmacao.",
                "- Operacoes destrutivas permanecem bloqueadas por padrao.",
                "- Coordenadas devem ser region/window-relative quando possivel.",
                "",
            ]
        )

    def capability_write_policy(self, side_effects: str) -> str:
        mapping = {
            "read-only": "read_only",
            "navigation": "confirm",
            "data-entry": "confirm",
            "external-write": "confirm",
            "destructive": "blocked_by_default",
        }
        return mapping[side_effects]

    def side_effect_guardrails(self, side_effects: str) -> list[str]:
        guardrails = {
            "read-only": ["Dry-run shows target, window and planned visual checks."],
            "navigation": ["Require --execute --confirm after dry-run and target-window review."],
            "data-entry": ["Require confirmation, screenshots and no plaintext credentials."],
            "external-write": ["Require explicit runtime confirmation and external approval."],
            "destructive": ["Blocked by default; require separate risk decision."],
        }
        return guardrails[side_effects]

    def automation_summary(self, spec: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": spec["automation_name"],
            "slug": spec["automation_slug"],
            "purpose": spec["purpose"],
            "target_app": spec["target_app"],
            "target_window": spec["target_window"],
        }

    def public_file_plan(self, files: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return [{"path": path, "bytes": len(content.encode("utf-8"))} for path, content in files]

    def open_questions(self, spec: dict[str, Any]) -> list[str]:
        questions: list[str] = []
        if spec["coordinates_policy"] == "absolute-last-resort":
            questions.append("Qual regiao segura limita as coordenadas absolutas?")
        if spec["side_effects"] != "read-only":
            questions.append("Qual ambiente seguro valida que a automacao nao alterara dados reais indevidamente?")
        if not spec["screen_preconditions"]:
            questions.append("Quais sinais visuais confirmam que a tela alvo esta pronta?")
        return questions

    def question_for_missing_field(self, field: str) -> str:
        questions = {
            "automation_name": "Qual sera o nome da automacao desktop?",
            "purpose": "Qual tarefa desktop a automacao deve resolver?",
            "target_app": "Qual aplicativo desktop sera controlado?",
            "target_window": "Qual titulo ou identificador da janela alvo?",
            "platform": "Qual plataforma sera usada: macos, windows, linux ou cross-platform?",
            "steps": "Quais passos visuais a automacao executa?",
            "screen_preconditions": "Quais pre-condicoes visuais devem existir antes da execucao?",
            "verification_strategy": "Como o script verifica que a acao produziu o estado esperado?",
            "safer_alternatives_checked": "Quais alternativas mais seguras foram checadas e indisponibilizadas?",
            "user_accepts_visual_risk": "O usuario aceitou explicitamente o risco visual?",
            "side_effects": "Qual classe de side effects sera usada?",
            "coordinates_policy": "Qual politica de coordenadas sera usada?",
        }
        return questions.get(field, f"Informe o campo `{field}`.")

    def markdown_list(self, values: list[str], *, fallback: str) -> str:
        clean = [value for value in values if value]
        if not clean:
            return f"- {fallback}"
        return "\n".join(f"- {value}" for value in clean)

    def title_from_id(self, value: str) -> str:
        return " ".join(part.capitalize() for part in value.split("-"))

    def slugify(self, value: str) -> str:
        slug = SLUG_PATTERN.sub("-", value.lower()).strip("-")
        return slug or "pyautogui-automation"

    def as_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "sim"}

    def iter_key_values(self, value: Any):
        if isinstance(value, dict):
            for key, child in value.items():
                yield str(key), child
                yield from self.iter_key_values(child)
        elif isinstance(value, list):
            for child in value:
                yield from self.iter_key_values(child)

    def is_inside(self, root: Path, target: Path) -> bool:
        try:
            target.relative_to(root.resolve())
            return True
        except ValueError:
            return False
