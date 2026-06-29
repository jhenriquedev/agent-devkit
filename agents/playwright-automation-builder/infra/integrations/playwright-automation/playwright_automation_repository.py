"""Repository for deterministic Playwright automation generation."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


REQUIRED_SPEC_FIELDS = (
    "automation_name",
    "purpose",
    "browser",
    "selectors",
    "steps",
    "assertions",
    "auth_strategy",
    "side_effects",
)
BROWSERS = {"chromium", "firefox", "webkit"}
AUTH_STRATEGIES = {"none", "env", "manual", "storage-state"}
SIDE_EFFECTS = {"read-only", "form-submit", "external-write", "destructive"}
ARTIFACTS = {"screenshot", "trace", "video", "console-log", "network-summary", "report"}
SELECTOR_KINDS = {"role", "label", "text", "test_id", "css"}
STABLE_SELECTOR_KINDS = {"role", "label", "text", "test_id"}
FORBIDDEN_MARKER_PATTERN = re.compile(r"\b(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)\b\s*[:=]", re.IGNORECASE)
KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class PlaywrightAutomationError(RuntimeError):
    """Raised when the builder cannot read or process an input spec."""


class PlaywrightAutomationRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[5]

    def plan_playwright_automation(self, *, spec_path: Path) -> dict[str, Any]:
        spec = self.load_spec(spec_path)
        spec_result = self.validate_spec(spec)
        if spec_result["status"] != "ok":
            return spec_result

        normalized = self.normalize_spec(spec)
        blocked = self.detect_forbidden_content(normalized)
        if blocked:
            return blocked

        files = self.build_playwright_files(normalized)
        return {
            "kind": "playwright-automation-plan",
            "status": "ok",
            "automation": self.automation_summary(normalized),
            "browser": normalized["browser"],
            "auth_strategy": normalized["auth_strategy"],
            "side_effects": normalized["side_effects"],
            "write_policy": "read_only",
            "planned_artifacts": self.public_file_plan(files),
            "runtime_artifacts": self.runtime_artifacts(normalized),
            "guardrails": self.side_effect_guardrails(normalized["side_effects"]),
            "selector_warnings": self.selector_warnings(normalized["selectors"]),
            "questions": self.open_questions(normalized),
        }

    def generate_playwright_script(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_playwright_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        content = self.render_playwright_script(spec)
        return {
            "kind": "playwright-script",
            "status": "ok",
            "automation": self.automation_summary(spec),
            "artifact": "playwright_automation.py",
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "write_policy": "output_only",
        }

    def generate_playwright_project_files(
        self,
        *,
        spec_path: Path,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_playwright_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "playwright-project-files",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }

        target_root = Path(str(target_project)).expanduser().resolve()
        files = self.build_playwright_files(spec, base_dir=spec["automation_slug"])
        return self.write_or_plan_files(
            kind="playwright-project-files",
            files=files,
            target_root=target_root,
            execute=execute,
            allow_overwrite=allow_overwrite,
            extra={"automation": self.automation_summary(spec), "side_effects": spec["side_effects"]},
        )

    def run_playwright_check(
        self,
        *,
        spec_path: Path,
        execute: bool = False,
        confirm: bool = False,
        headless: bool = True,
    ) -> dict[str, Any]:
        plan = self.plan_playwright_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        if not execute:
            return {
                "kind": "playwright-check",
                "status": "planned",
                "dry_run": True,
                "automation": self.automation_summary(spec),
                "command": "python playwright_automation.py --execute --headless",
                "write_policy": "dry_run",
                "next_steps": ["Review the dry-run plan before running with --execute."],
            }
        if spec["side_effects"] != "read-only" and not confirm:
            return {
                "kind": "playwright-check",
                "status": "blocked",
                "reason": "confirmation_required",
                "side_effects": spec["side_effects"],
                "risks": ["Playwright automation with side effects requires --confirm."],
                "write_policy": "confirm",
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "playwright_automation.py"
            script_path.write_text(self.render_playwright_script(spec), encoding="utf-8")
            args = [sys.executable, str(script_path), "--execute"]
            if confirm:
                args.append("--confirm")
            if headless:
                args.append("--headless")
            process = subprocess.run(
                args,
                cwd=tmpdir,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
            )
        return {
            "kind": "playwright-check",
            "status": "ok" if process.returncode == 0 else "failed",
            "dry_run": False,
            "exit_code": process.returncode,
            "stdout": safe_tail(process.stdout),
            "stderr": safe_tail(process.stderr),
            "write_policy": "confirm",
        }

    def review_playwright_artifacts(self, *, paths: list[Path], text: str | None = None) -> dict[str, Any]:
        findings: list[str] = []
        artifacts: list[dict[str, Any]] = []
        for path in paths:
            resolved = path.expanduser().resolve()
            item = {
                "path": str(resolved),
                "exists": resolved.exists(),
                "suffix": resolved.suffix.lower(),
                "sensitive": self.artifact_may_be_sensitive(resolved),
            }
            if not resolved.exists():
                findings.append(f"artifact missing: {path}")
            artifacts.append(item)
        if text is not None:
            findings.extend(self.review_playwright_script(text=text, side_effects="read-only")["findings"])
        if not artifacts and text is None:
            findings.append("no artifacts or script text provided")
        return {
            "kind": "playwright-artifact-review",
            "status": "ok" if not findings else "failed",
            "valid": not findings,
            "artifacts": artifacts,
            "findings": findings,
            "write_policy": "read_only",
        }

    def review_playwright_script(self, *, text: str, side_effects: str = "read-only") -> dict[str, Any]:
        normalized_side_effects = str(side_effects or "read-only").strip()
        findings: list[str] = []
        lower_text = text.lower()
        if not text.strip():
            findings.append("playwright script is empty")
        if "sync_playwright" not in text:
            findings.append("playwright script must use Playwright sync API or clearly equivalent runtime")
        for flag in ("--dry-run", "--execute", "--headless", "--browser", "--timeout", "--screenshot-dir", "--trace-dir"):
            if flag not in text:
                findings.append(f"playwright script must expose {flag}")
        if "screenshot(" not in lower_text:
            findings.append("playwright script must capture screenshots")
        if "tracing.start" not in lower_text or "tracing.stop" not in lower_text:
            findings.append("playwright script should support traces")
        if "time.sleep" in lower_text:
            findings.append("playwright script must not use time.sleep as primary waiting")
        if normalized_side_effects != "read-only" and "--confirm" not in text:
            findings.append("playwright script with side effects must require --confirm")
        if "return 0" not in text and "sys.exit(0)" not in text:
            findings.append("playwright script should return a predictable success exit code")
        if self.detect_text_forbidden_content(text):
            findings.append("playwright script contains a secret marker")
        valid = not findings
        return {
            "kind": "playwright-review",
            "status": "ok" if valid else "failed",
            "valid": valid,
            "side_effects": normalized_side_effects,
            "findings": findings,
            "write_policy": "read_only",
        }

    def wrap_playwright_as_capability(
        self,
        *,
        spec_path: Path,
        agent_id: str,
        capability_id: str,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_playwright_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        if not KEBAB_CASE.match(agent_id):
            return {
                "kind": "playwright-capability-wrapper",
                "status": "blocked",
                "reason": "invalid_agent_id",
                "risks": ["agent-id must be kebab-case."],
            }
        if not KEBAB_CASE.match(capability_id):
            return {
                "kind": "playwright-capability-wrapper",
                "status": "blocked",
                "reason": "invalid_capability_id",
                "risks": ["capability-id must be kebab-case."],
            }

        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "playwright-capability-wrapper",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }

        target_root = Path(str(target_project)).expanduser().resolve()
        files = self.build_capability_wrapper_files(spec, agent_id=agent_id, capability_id=capability_id)
        return self.write_or_plan_files(
            kind="playwright-capability-wrapper",
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
            raise PlaywrightAutomationError(f"spec not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            payload = json.loads(text)
        else:
            payload = yaml.safe_load(text) or {}
        if not isinstance(payload, dict):
            raise PlaywrightAutomationError("spec must be a mapping")
        return payload

    def validate_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        missing = [
            field
            for field in REQUIRED_SPEC_FIELDS
            if field not in spec or spec.get(field) is None or spec.get(field) == ""
        ]
        if not spec.get("target_url") and not spec.get("target_description"):
            missing.append("target_url_or_description")
        if missing:
            return {
                "kind": "playwright-automation-plan",
                "status": "needs-input",
                "missing_fields": missing,
                "questions": [self.question_for_missing_field(field) for field in missing],
            }
        for field in ("selectors", "steps", "assertions", "artifacts", "quality_gates"):
            if spec.get(field) is not None and not isinstance(spec[field], list):
                return {
                    "kind": "playwright-automation-plan",
                    "status": "blocked",
                    "reason": "invalid_list_field",
                    "field": field,
                    "risks": [f"{field} must be a list when provided."],
                }
        browser = str(spec.get("browser") or "").strip().lower()
        if browser not in BROWSERS:
            return {
                "kind": "playwright-automation-plan",
                "status": "blocked",
                "reason": "unsupported_browser",
                "supported_values": sorted(BROWSERS),
            }
        auth_strategy = str(spec.get("auth_strategy") or "").strip()
        if auth_strategy not in AUTH_STRATEGIES:
            return {
                "kind": "playwright-automation-plan",
                "status": "blocked",
                "reason": "unsupported_auth_strategy",
                "supported_values": sorted(AUTH_STRATEGIES),
            }
        side_effects = str(spec.get("side_effects") or "").strip()
        if side_effects not in SIDE_EFFECTS:
            return {
                "kind": "playwright-automation-plan",
                "status": "blocked",
                "reason": "invalid_side_effects",
                "supported_values": sorted(SIDE_EFFECTS),
            }
        return {"status": "ok"}

    def normalize_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(spec)
        normalized["automation_name"] = " ".join(str(spec["automation_name"]).split())
        normalized["automation_slug"] = self.slugify(normalized["automation_name"])
        normalized["purpose"] = " ".join(str(spec["purpose"]).split())
        normalized["target_url"] = str(spec.get("target_url") or "").strip()
        normalized["target_description"] = " ".join(str(spec.get("target_description") or "").split())
        normalized["browser"] = str(spec["browser"]).strip().lower()
        normalized["auth_strategy"] = str(spec["auth_strategy"]).strip()
        normalized["side_effects"] = str(spec["side_effects"]).strip()
        normalized["storage_state_env"] = str(spec.get("storage_state_env") or "").strip()
        normalized["selectors"] = [self.normalize_selector(item) for item in spec.get("selectors") or []]
        normalized["steps"] = [str(item).strip() for item in spec.get("steps") or []]
        normalized["assertions"] = [str(item).strip() for item in spec.get("assertions") or []]
        normalized["artifacts"] = self.normalize_artifacts(spec.get("artifacts") or ["screenshot", "trace", "report"])
        normalized["quality_gates"] = [str(item).strip() for item in spec.get("quality_gates") or []]
        if spec.get("target_project"):
            normalized["target_project"] = str(spec["target_project"]).strip()
        return normalized

    def detect_forbidden_content(self, spec: dict[str, Any]) -> dict[str, Any] | None:
        for key, value in self.iter_key_values(spec):
            if key in {"target_url", "storage_state_env"}:
                continue
            if isinstance(value, str) and self.detect_text_forbidden_content(value):
                return {
                    "kind": "playwright-automation-plan",
                    "status": "blocked",
                    "reason": "forbidden_sensitive_marker",
                    "risks": ["Spec contains text that looks like a hardcoded secret."],
                }
        return None

    def detect_text_forbidden_content(self, value: str) -> bool:
        return bool(FORBIDDEN_MARKER_PATTERN.search(value))

    def build_playwright_files(self, spec: dict[str, Any], *, base_dir: str = "") -> list[tuple[str, str]]:
        prefix = f"{base_dir}/" if base_dir else ""
        return [
            (f"{prefix}playwright_automation.py", self.render_playwright_script(spec)),
            (f"{prefix}README.md", self.render_readme(spec)),
            (f"{prefix}requirements.txt", "playwright>=1.44\n"),
            (f"{prefix}tests/test_playwright_automation.py", self.render_playwright_test(spec)),
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
            (f"{base}/runner.py", self.render_playwright_script(spec)),
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
                "next_steps": ["Rerun with --allow-overwrite only after reviewing existing files."],
            }

        written_files = []
        for _relative_path, target, content in checked_files:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written_files.append({"path": str(target), "bytes": len(content.encode("utf-8"))})

        return {"kind": kind, "status": "written", "dry_run": False, "target_project": str(target_root), "written_files": written_files, **extra}

    def render_playwright_script(self, spec: dict[str, Any]) -> str:
        selectors = [
            {
                "name": selector["name"],
                "kind": selector["kind"],
                "value": selector["value"],
                "name_value": selector.get("name_value") or "",
            }
            for selector in spec["selectors"]
        ]
        needs_confirmation = spec["side_effects"] != "read-only"
        confirmation_block = [
            "    if args.execute and not args.confirm:",
            "        logger.error(\"real Playwright side effects require --confirm after reviewing --dry-run output\")",
            "        return 2",
        ]
        if not needs_confirmation:
            confirmation_block = [
                "    if args.execute and not args.confirm:",
                "        logger.info(\"--confirm not required for read-only Playwright automation\")",
            ]

        return "\n".join(
            [
                "#!/usr/bin/env python3",
                f'"""Playwright automation: {spec["automation_name"]}."""',
                "",
                "from __future__ import annotations",
                "",
                "import argparse",
                "import json",
                "import logging",
                "import os",
                "from pathlib import Path",
                "",
                f"TARGET_URL = {spec['target_url']!r}",
                f"SELECTORS = {selectors!r}",
                f"STORAGE_STATE_ENV = {spec['storage_state_env']!r}",
                "",
                "",
                "def build_parser() -> argparse.ArgumentParser:",
                f"    parser = argparse.ArgumentParser(description={spec['purpose']!r})",
                "    parser.add_argument(\"--dry-run\", action=\"store_true\", help=\"show planned browser actions without opening a browser\")",
                "    parser.add_argument(\"--execute\", action=\"store_true\", help=\"open browser and run the automation\")",
                "    parser.add_argument(\"--confirm\", action=\"store_true\", help=\"confirm real browser side effects after dry-run review\")",
                "    parser.add_argument(\"--headless\", action=\"store_true\", help=\"run browser headless\")",
                f"    parser.add_argument(\"--browser\", choices={sorted(BROWSERS)!r}, default={spec['browser']!r})",
                "    parser.add_argument(\"--timeout\", type=int, default=20)",
                "    parser.add_argument(\"--screenshot-dir\", default=\"playwright-artifacts/screenshots\")",
                "    parser.add_argument(\"--trace-dir\", default=\"playwright-artifacts/traces\")",
                "    parser.add_argument(\"--storage-state\", help=\"optional path to local Playwright storage state\")",
                "    return parser",
                "",
                "",
                "def planned_actions(args: argparse.Namespace) -> dict:",
                "    return {",
                f"        \"automation\": {spec['automation_slug']!r},",
                "        \"browser\": args.browser,",
                "        \"target_url\": TARGET_URL or \"<target-description-only>\",",
                "        \"selectors\": [selector[\"name\"] for selector in SELECTORS],",
                f"        \"side_effects\": {spec['side_effects']!r},",
                f"        \"artifacts\": {spec['artifacts']!r},",
                "    }",
                "",
                "",
                "def playwright_imports():",
                "    from playwright.sync_api import expect, sync_playwright",
                "    return expect, sync_playwright",
                "",
                "",
                "def selector_locator(page, selector: dict):",
                "    kind = selector[\"kind\"]",
                "    value = selector[\"value\"]",
                "    accessible_name = selector.get(\"name_value\") or None",
                "    if kind == \"role\":",
                "        return page.get_by_role(value, name=accessible_name)",
                "    if kind == \"label\":",
                "        return page.get_by_label(value)",
                "    if kind == \"text\":",
                "        return page.get_by_text(value)",
                "    if kind == \"test_id\":",
                "        return page.get_by_test_id(value)",
                "    return page.locator(value)",
                "",
                "",
                "def storage_state_path(args: argparse.Namespace) -> str | None:",
                "    candidate = args.storage_state or (os.environ.get(STORAGE_STATE_ENV) if STORAGE_STATE_ENV else None)",
                "    return candidate or None",
                "",
                "",
                "def run_browser(args: argparse.Namespace) -> dict:",
                "    expect, sync_playwright = playwright_imports()",
                "    screenshot_dir = Path(args.screenshot_dir)",
                "    trace_dir = Path(args.trace_dir)",
                "    screenshot_dir.mkdir(parents=True, exist_ok=True)",
                "    trace_dir.mkdir(parents=True, exist_ok=True)",
                "    with sync_playwright() as playwright:",
                "        browser_type = getattr(playwright, args.browser)",
                "        browser = browser_type.launch(headless=args.headless)",
                "        context_kwargs = {}",
                "        state = storage_state_path(args)",
                "        if state:",
                "            context_kwargs[\"storage_state\"] = state",
                "        context = browser.new_context(**context_kwargs)",
                "        context.tracing.start(screenshots=True, snapshots=True, sources=False)",
                "        page = context.new_page()",
                "        page.set_default_timeout(args.timeout * 1000)",
                "        try:",
                "            if TARGET_URL:",
                "                page.goto(TARGET_URL, wait_until=\"domcontentloaded\")",
                "            checked = []",
                "            for selector in SELECTORS:",
                "                locator = selector_locator(page, selector)",
                "                expect(locator.first).to_be_visible()",
                "                checked.append(selector[\"name\"])",
                "            screenshot = screenshot_dir / \"success.png\"",
                "            page.screenshot(path=str(screenshot), full_page=True)",
                "            trace = trace_dir / \"trace.zip\"",
                "            context.tracing.stop(path=str(trace))",
                "            return {\"status\": \"ok\", \"checked_selectors\": checked, \"screenshot\": str(screenshot), \"trace\": str(trace)}",
                "        except Exception as exc:",
                "            screenshot = screenshot_dir / \"failure.png\"",
                "            page.screenshot(path=str(screenshot), full_page=True)",
                "            trace = trace_dir / \"failure-trace.zip\"",
                "            context.tracing.stop(path=str(trace))",
                "            return {\"status\": \"failed\", \"error\": str(exc), \"screenshot\": str(screenshot), \"trace\": str(trace)}",
                "        finally:",
                "            context.close()",
                "            browser.close()",
                "",
                "",
                "def main(argv: list[str] | None = None) -> int:",
                "    parser = build_parser()",
                "    args = parser.parse_args(argv)",
                "    logging.basicConfig(level=logging.INFO, format=\"%(levelname)s %(message)s\")",
                "    logger = logging.getLogger(\"playwright-automation\")",
                "    if args.execute and args.dry_run:",
                "        logger.error(\"choose either --dry-run or --execute\")",
                "        return 2",
                *confirmation_block,
                "    if not args.execute:",
                "        print(json.dumps({\"dry_run\": True, \"plan\": planned_actions(args)}, indent=2))",
                "        return 0",
                "    result = run_browser(args)",
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
        selectors = self.markdown_list([selector["name"] for selector in spec["selectors"]], fallback="No selectors.")
        assertions = self.markdown_list(spec["assertions"], fallback="Review generated assertions.")
        artifacts = self.markdown_list(spec["artifacts"], fallback="No artifacts.")
        return "\n".join(
            [
                f"# {spec['automation_name']}",
                "",
                spec["purpose"],
                "",
                "## Usage",
                "",
                "```bash",
                "python playwright_automation.py --dry-run",
                "python playwright_automation.py --execute --headless",
                "```",
                "",
                "## Selectors",
                "",
                selectors,
                "",
                "## Assertions",
                "",
                assertions,
                "",
                "## Artifacts",
                "",
                artifacts,
                "",
                "## Guardrails",
                "",
                "- Prefer role, label, text or test id selectors.",
                "- Capture screenshot and trace for review.",
                "- Do not hardcode credentials.",
                "- Use Selenium only when WebDriver/Grid compatibility is required.",
                "",
            ]
        )

    def render_playwright_test(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "import json",
                "import subprocess",
                "import sys",
                "from pathlib import Path",
                "",
                "",
                "def test_playwright_automation_dry_run_returns_plan_without_browser():",
                "    script = Path(__file__).resolve().parents[1] / \"playwright_automation.py\"",
                "    result = subprocess.run([sys.executable, str(script), \"--dry-run\"], text=True, capture_output=True, check=False)",
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
            "inputs": {"required": [], "optional": ["dry-run", "execute", "confirm", "headless", "browser"]},
            "outputs": {"artifacts": ["playwright-result.json", "success.png", "failure.png", "trace.zip"]},
            "write_policy": self.capability_write_policy(spec["side_effects"]),
        }
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)

    def render_capability_workflow(self, spec: dict[str, Any], *, capability_id: str) -> str:
        return "\n".join(
            [
                "# Workflow",
                "",
                f"1. Executar `{capability_id}` em dry-run por padrao.",
                "2. Revisar target, seletores, assertions e artifacts.",
                "3. Executar com `--execute --confirm` apenas quando houver autorizacao para side effects.",
                "4. Retornar JSON, screenshot e trace.",
                "",
            ]
        )

    def render_capability_decision_rules(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "# Decision Rules",
                "",
                f"- Side effects classificados como `{spec['side_effects']}`.",
                "- Preferir seletores por role, label, text ou test id.",
                "- Storage state sensivel nao deve ser versionado.",
                "- Escrita, submit ou alteracao externa exige confirmacao.",
                "- Selenium deve ser usado apenas com requisito WebDriver/Grid/legado.",
                "",
            ]
        )

    def normalize_selector(self, value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            return {"name": "invalid", "kind": "css", "value": str(value), "name_value": ""}
        selector = {
            "name": str(value.get("name") or "selector").strip(),
            "kind": str(value.get("kind") or value.get("by") or "css").strip(),
            "value": str(value.get("value") or "").strip(),
            "name_value": str(value.get("name_value") or value.get("accessible_name") or "").strip(),
        }
        if selector["kind"] not in SELECTOR_KINDS:
            selector["kind"] = "css"
        return selector

    def normalize_artifacts(self, values: Any) -> list[str]:
        raw = values if isinstance(values, list) else []
        normalized: list[str] = []
        for item in raw:
            value = str(item or "").strip()
            if value in ARTIFACTS and value not in normalized:
                normalized.append(value)
        return normalized or ["screenshot", "trace", "report"]

    def selector_warnings(self, selectors: list[dict[str, str]]) -> list[str]:
        warnings = []
        for selector in selectors:
            if selector["kind"] not in STABLE_SELECTOR_KINDS:
                warnings.append(f"selector {selector['name']} uses {selector['kind']}; prefer role, label, text or test_id")
            if selector["kind"] == "css" and re.search(r"\.[a-z0-9_-]{12,}", selector["value"], re.IGNORECASE):
                warnings.append(f"selector {selector['name']} may use a generated class")
        return warnings

    def runtime_artifacts(self, spec: dict[str, Any]) -> list[dict[str, Any]]:
        sensitive = spec["auth_strategy"] in {"manual", "storage-state"}
        return [
            {"path": "playwright-artifacts/screenshots/*.png", "kind": "screenshot", "sensitive": sensitive},
            {"path": "playwright-artifacts/traces/*.zip", "kind": "trace", "sensitive": sensitive},
            {"path": "playwright-result.json", "kind": "json", "sensitive": sensitive},
        ]

    def artifact_may_be_sensitive(self, path: Path) -> bool:
        lower = str(path).lower()
        return any(marker in lower for marker in ("storage", "state", "trace", "screenshot", "auth", "login"))

    def capability_write_policy(self, side_effects: str) -> str:
        mapping = {
            "read-only": "read_only",
            "form-submit": "confirm",
            "external-write": "confirm",
            "destructive": "blocked_by_default",
        }
        return mapping[side_effects]

    def side_effect_guardrails(self, side_effects: str) -> list[str]:
        guardrails = {
            "read-only": ["Dry-run shows target and selectors without opening browser."],
            "form-submit": ["Require --execute --confirm after dry-run review."],
            "external-write": ["Require explicit runtime confirmation and external approval."],
            "destructive": ["Blocked by default; require separate risk decision."],
        }
        return guardrails[side_effects]

    def automation_summary(self, spec: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": spec["automation_name"],
            "slug": spec["automation_slug"],
            "purpose": spec["purpose"],
            "target": spec["target_url"] or spec["target_description"],
        }

    def public_file_plan(self, files: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return [{"path": path, "bytes": len(content.encode("utf-8"))} for path, content in files]

    def open_questions(self, spec: dict[str, Any]) -> list[str]:
        questions: list[str] = []
        if spec["auth_strategy"] in {"env", "storage-state"}:
            questions.append("Quais env vars ou storage state local serao referenciados sem expor valores?")
        if spec["side_effects"] != "read-only":
            questions.append("Qual ambiente sandbox confirma que a automacao nao afetara dados reais?")
        if self.selector_warnings(spec["selectors"]):
            questions.append("Ha seletores por role, label, text ou test id que substituam CSS fragil?")
        return questions

    def question_for_missing_field(self, field: str) -> str:
        questions = {
            "automation_name": "Qual sera o nome da automacao Playwright?",
            "purpose": "Qual tarefa web a automacao deve resolver?",
            "target_url_or_description": "Qual URL ou descricao do alvo Playwright?",
            "browser": "Qual browser Playwright sera usado?",
            "selectors": "Quais seletores estaveis serao usados?",
            "steps": "Quais passos a automacao executa?",
            "assertions": "Quais assertions verificam sucesso?",
            "auth_strategy": "Qual estrategia de autenticacao sera usada?",
            "side_effects": "Qual classificacao de side effects se aplica?",
        }
        return questions.get(field, f"Informe o campo obrigatorio {field}.")

    def markdown_list(self, values: list[str], *, fallback: str) -> str:
        if not values:
            return f"- {fallback}"
        return "\n".join(f"- {value}" for value in values)

    def slugify(self, value: str) -> str:
        slug = SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
        return slug or "playwright-automation"

    def title_from_id(self, value: str) -> str:
        return " ".join(part.capitalize() for part in value.split("-"))

    def iter_key_values(self, value: Any, *, parent_key: str = ""):
        if isinstance(value, dict):
            for key, item in value.items():
                yield from self.iter_key_values(item, parent_key=str(key))
        elif isinstance(value, list):
            for item in value:
                yield from self.iter_key_values(item, parent_key=parent_key)
        else:
            yield parent_key, value

    def is_inside(self, root: Path, target: Path) -> bool:
        try:
            target.relative_to(root)
            return True
        except ValueError:
            return False


def safe_tail(value: str, limit: int = 2000) -> str:
    text = value or ""
    return text[-limit:]
