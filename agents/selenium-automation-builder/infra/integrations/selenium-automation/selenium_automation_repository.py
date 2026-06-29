"""Repository for deterministic Selenium automation generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


REQUIRED_SPEC_FIELDS = (
    "automation_name",
    "purpose",
    "browser",
    "selectors",
    "steps",
    "auth_strategy",
    "side_effects",
    "selenium_reasons",
)
BROWSERS = {"chrome", "firefox", "edge"}
AUTH_STRATEGIES = {"none", "env", "manual", "existing-session"}
SIDE_EFFECTS = {"read-only", "form-submit", "external-write", "destructive"}
SELENIUM_REASONS = {
    "existing-selenium",
    "selenium-grid",
    "remote-browser",
    "webdriver-required",
    "legacy-project",
    "browser-extension",
    "team-standard",
    "playwright-not-allowed",
}
SELECTOR_BY_MAP = {
    "css": "CSS_SELECTOR",
    "id": "ID",
    "name": "NAME",
    "xpath": "XPATH",
    "link_text": "LINK_TEXT",
    "partial_link_text": "PARTIAL_LINK_TEXT",
    "tag": "TAG_NAME",
}
FORBIDDEN_MARKER_PATTERN = re.compile(r"\b(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)\b\s*[:=]")
KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class SeleniumAutomationError(RuntimeError):
    """Raised when the builder cannot read or process an input spec."""


class SeleniumAutomationRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[5]

    def plan_selenium_automation(self, *, spec_path: Path) -> dict[str, Any]:
        spec = self.load_spec(spec_path)
        spec_result = self.validate_spec(spec)
        if spec_result["status"] != "ok":
            return spec_result

        normalized = self.normalize_spec(spec)
        blocked = self.detect_forbidden_content(normalized)
        if blocked:
            return blocked

        reason_result = self.validate_selenium_reasons(normalized["selenium_reasons"])
        if reason_result["status"] != "ok":
            return reason_result

        files = self.build_selenium_files(normalized)
        return {
            "kind": "selenium-automation-plan",
            "status": "ok",
            "automation": self.automation_summary(normalized),
            "browser": normalized["browser"],
            "side_effects": normalized["side_effects"],
            "write_policy": "read_only",
            "selenium_reasons": normalized["selenium_reasons"],
            "planned_artifacts": self.public_file_plan(files),
            "guardrails": self.side_effect_guardrails(normalized["side_effects"]),
            "questions": self.open_questions(normalized),
        }

    def generate_selenium_script(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_selenium_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        content = self.render_selenium_script(spec)
        return {
            "kind": "selenium-script",
            "status": "ok",
            "automation": self.automation_summary(spec),
            "artifact": "selenium_automation.py",
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "write_policy": "output_only",
        }

    def generate_selenium_project_files(
        self,
        *,
        spec_path: Path,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_selenium_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "selenium-project-files",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }

        target_root = Path(str(target_project)).expanduser().resolve()
        files = self.build_selenium_files(spec, base_dir=spec["automation_slug"])
        return self.write_or_plan_files(
            kind="selenium-project-files",
            files=files,
            target_root=target_root,
            execute=execute,
            allow_overwrite=allow_overwrite,
            extra={"automation": self.automation_summary(spec), "side_effects": spec["side_effects"]},
        )

    def review_selenium_script(self, *, text: str, side_effects: str = "read-only") -> dict[str, Any]:
        normalized_side_effects = str(side_effects or "read-only").strip()
        findings: list[str] = []
        if not text.strip():
            findings.append("selenium script is empty")
        lower_text = text.lower()
        if "webdriverwait" not in lower_text:
            findings.append("selenium script must use WebDriverWait explicit waits")
        if "time.sleep" in lower_text:
            findings.append("selenium script must not use time.sleep as primary waiting")
        for flag in ("--dry-run", "--headless", "--browser", "--timeout", "--screenshot-dir"):
            if flag not in text:
                findings.append(f"selenium script must expose {flag}")
        if "save_screenshot" not in text:
            findings.append("selenium script must capture screenshot on failure")
        if normalized_side_effects != "read-only" and "--confirm" not in text:
            findings.append("selenium script with side effects must require --confirm")
        if "return 0" not in text and "sys.exit(0)" not in text:
            findings.append("selenium script should return a predictable success exit code")
        if self.detect_text_forbidden_content(text):
            findings.append("selenium script contains a secret marker")

        valid = not findings
        return {
            "kind": "selenium-review",
            "status": "ok" if valid else "failed",
            "valid": valid,
            "side_effects": normalized_side_effects,
            "findings": findings,
            "write_policy": "read_only",
        }

    def wrap_selenium_as_capability(
        self,
        *,
        spec_path: Path,
        agent_id: str,
        capability_id: str,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_selenium_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        if not KEBAB_CASE.match(agent_id):
            return {
                "kind": "selenium-capability-wrapper",
                "status": "blocked",
                "reason": "invalid_agent_id",
                "risks": ["agent-id must be kebab-case."],
            }
        if not KEBAB_CASE.match(capability_id):
            return {
                "kind": "selenium-capability-wrapper",
                "status": "blocked",
                "reason": "invalid_capability_id",
                "risks": ["capability-id must be kebab-case."],
            }

        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "selenium-capability-wrapper",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }

        target_root = Path(str(target_project)).expanduser().resolve()
        files = self.build_capability_wrapper_files(spec, agent_id=agent_id, capability_id=capability_id)
        return self.write_or_plan_files(
            kind="selenium-capability-wrapper",
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
            raise SeleniumAutomationError(f"spec not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            payload = json.loads(text)
        else:
            payload = yaml.safe_load(text) or {}
        if not isinstance(payload, dict):
            raise SeleniumAutomationError("spec must be a mapping")
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
                "kind": "selenium-automation-plan",
                "status": "needs-input",
                "missing_fields": missing,
                "questions": [self.question_for_missing_field(field) for field in missing],
            }
        for field in ("selectors", "steps", "selenium_reasons", "quality_gates"):
            if spec.get(field) is not None and not isinstance(spec[field], list):
                return {
                    "kind": "selenium-automation-plan",
                    "status": "blocked",
                    "reason": "invalid_list_field",
                    "field": field,
                    "risks": [f"{field} must be a list when provided."],
                }
        browser = str(spec.get("browser") or "").strip().lower()
        if browser not in BROWSERS:
            return {
                "kind": "selenium-automation-plan",
                "status": "blocked",
                "reason": "unsupported_browser",
                "supported_values": sorted(BROWSERS),
            }
        auth_strategy = str(spec.get("auth_strategy") or "").strip()
        if auth_strategy not in AUTH_STRATEGIES:
            return {
                "kind": "selenium-automation-plan",
                "status": "blocked",
                "reason": "unsupported_auth_strategy",
                "supported_values": sorted(AUTH_STRATEGIES),
            }
        side_effects = str(spec.get("side_effects") or "").strip()
        if side_effects not in SIDE_EFFECTS:
            return {
                "kind": "selenium-automation-plan",
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
        normalized["remote_url_env"] = str(spec.get("remote_url_env") or "").strip()
        normalized["auth_strategy"] = str(spec["auth_strategy"]).strip()
        normalized["side_effects"] = str(spec["side_effects"]).strip()
        normalized["selenium_reasons"] = [str(item).strip() for item in spec.get("selenium_reasons") or []]
        normalized["selectors"] = [self.normalize_selector(item) for item in spec.get("selectors") or []]
        normalized["steps"] = [str(item).strip() for item in spec.get("steps") or []]
        normalized["quality_gates"] = [str(item).strip() for item in spec.get("quality_gates") or []]
        if spec.get("target_project"):
            normalized["target_project"] = str(spec["target_project"]).strip()
        return normalized

    def validate_selenium_reasons(self, reasons: list[str]) -> dict[str, Any]:
        if not reasons:
            return {
                "kind": "selenium-automation-plan",
                "status": "needs-playwright-review",
                "reason": "selenium_not_justified",
                "risks": ["Selenium should not be the default for modern web automation."],
                "next_steps": ["Use problem 27 / Playwright unless WebDriver or Selenium compatibility is required."],
            }
        unknown = [reason for reason in reasons if reason not in SELENIUM_REASONS]
        if unknown:
            return {
                "kind": "selenium-automation-plan",
                "status": "blocked",
                "reason": "unsupported_selenium_reason",
                "unsupported_values": unknown,
                "supported_values": sorted(SELENIUM_REASONS),
            }
        return {"status": "ok"}

    def detect_forbidden_content(self, spec: dict[str, Any]) -> dict[str, Any] | None:
        for key, value in self.iter_key_values(spec):
            if key in {"target_url", "remote_url_env"}:
                continue
            if isinstance(value, str) and self.detect_text_forbidden_content(value):
                return {
                    "kind": "selenium-automation-plan",
                    "status": "blocked",
                    "reason": "forbidden_sensitive_marker",
                    "risks": ["Spec contains text that looks like a hardcoded secret."],
                }
        return None

    def detect_text_forbidden_content(self, value: str) -> bool:
        return bool(FORBIDDEN_MARKER_PATTERN.search(value))

    def build_selenium_files(self, spec: dict[str, Any], *, base_dir: str = "") -> list[tuple[str, str]]:
        prefix = f"{base_dir}/" if base_dir else ""
        return [
            (f"{prefix}selenium_automation.py", self.render_selenium_script(spec)),
            (f"{prefix}README.md", self.render_readme(spec)),
            (f"{prefix}requirements.txt", "selenium>=4.0\n"),
            (f"{prefix}tests/test_selenium_automation.py", self.render_selenium_test(spec)),
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
            (f"{base}/runner.py", self.render_selenium_script(spec)),
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

    def render_selenium_script(self, spec: dict[str, Any]) -> str:
        locators = [
            {
                "name": selector["name"],
                "by": selector["by"],
                "value": selector["value"],
            }
            for selector in spec["selectors"]
        ]
        needs_confirmation = spec["side_effects"] != "read-only"
        confirmation_block = [
            "    if args.execute and not args.confirm:",
            "        logger.error(\"real Selenium side effects require --confirm after reviewing --dry-run output\")",
            "        return 2",
        ]
        if not needs_confirmation:
            confirmation_block = [
                "    if args.execute and not args.confirm:",
                "        logger.info(\"--confirm not required for read-only Selenium automation\")",
            ]

        return "\n".join(
            [
                "#!/usr/bin/env python3",
                f'"""Selenium automation: {spec["automation_name"]}."""',
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
                f"REMOTE_URL_ENV = {spec['remote_url_env']!r}",
                f"LOCATORS = {locators!r}",
                "",
                "",
                "def build_parser() -> argparse.ArgumentParser:",
                f"    parser = argparse.ArgumentParser(description={spec['purpose']!r})",
                "    parser.add_argument(\"--dry-run\", action=\"store_true\", help=\"show planned browser actions without opening a browser\")",
                "    parser.add_argument(\"--execute\", action=\"store_true\", help=\"open browser and run the automation\")",
                "    parser.add_argument(\"--confirm\", action=\"store_true\", help=\"confirm real browser side effects after dry-run review\")",
                "    parser.add_argument(\"--headless\", action=\"store_true\", help=\"run browser headless\")",
                f"    parser.add_argument(\"--browser\", choices={sorted(BROWSERS)!r}, default={spec['browser']!r})",
                "    parser.add_argument(\"--remote-url\", help=\"optional Selenium Remote WebDriver URL\")",
                "    parser.add_argument(\"--timeout\", type=int, default=20)",
                "    parser.add_argument(\"--screenshot-dir\", default=\"selenium-artifacts\")",
                "    return parser",
                "",
                "",
                "def selenium_imports():",
                "    from selenium import webdriver",
                "    from selenium.webdriver.common.by import By",
                "    from selenium.webdriver.support import expected_conditions as EC",
                "    from selenium.webdriver.support.ui import WebDriverWait",
                "    return webdriver, By, EC, WebDriverWait",
                "",
                "",
                "def by_value(by_module, selector_kind: str):",
                "    mapping = {",
                "        \"css\": by_module.CSS_SELECTOR,",
                "        \"id\": by_module.ID,",
                "        \"name\": by_module.NAME,",
                "        \"xpath\": by_module.XPATH,",
                "        \"link_text\": by_module.LINK_TEXT,",
                "        \"partial_link_text\": by_module.PARTIAL_LINK_TEXT,",
                "        \"tag\": by_module.TAG_NAME,",
                "    }",
                "    return mapping[selector_kind]",
                "",
                "",
                "def build_options(webdriver, browser: str, headless: bool):",
                "    if browser == \"chrome\":",
                "        options = webdriver.ChromeOptions()",
                "    elif browser == \"firefox\":",
                "        options = webdriver.FirefoxOptions()",
                "    else:",
                "        options = webdriver.EdgeOptions()",
                "    if headless:",
                "        options.add_argument(\"--headless=new\")",
                "    return options",
                "",
                "",
                "def create_driver(args):",
                "    webdriver, by_module, expected_conditions, wait_class = selenium_imports()",
                "    options = build_options(webdriver, args.browser, args.headless)",
                "    remote_url = args.remote_url or (os.environ.get(REMOTE_URL_ENV) if REMOTE_URL_ENV else None)",
                "    if remote_url:",
                "        driver = webdriver.Remote(command_executor=remote_url, options=options)",
                "    elif args.browser == \"chrome\":",
                "        driver = webdriver.Chrome(options=options)",
                "    elif args.browser == \"firefox\":",
                "        driver = webdriver.Firefox(options=options)",
                "    else:",
                "        driver = webdriver.Edge(options=options)",
                "    return driver, by_module, expected_conditions, wait_class",
                "",
                "",
                "def planned_actions(args: argparse.Namespace) -> dict:",
                "    return {",
                f"        \"automation\": {spec['automation_slug']!r},",
                "        \"browser\": args.browser,",
                "        \"target_url\": TARGET_URL or \"<target-description-only>\",",
                "        \"remote\": bool(args.remote_url or (os.environ.get(REMOTE_URL_ENV) if REMOTE_URL_ENV else None)),",
                "        \"locators\": [locator[\"name\"] for locator in LOCATORS],",
                f"        \"side_effects\": {spec['side_effects']!r},",
                "    }",
                "",
                "",
                "def run_browser(args: argparse.Namespace) -> dict:",
                "    driver, by_module, expected_conditions, wait_class = create_driver(args)",
                "    screenshot_dir = Path(args.screenshot_dir)",
                "    screenshot_dir.mkdir(parents=True, exist_ok=True)",
                "    try:",
                "        if TARGET_URL:",
                "            driver.get(TARGET_URL)",
                "        for locator in LOCATORS:",
                "            wait_class(driver, args.timeout).until(",
                "                expected_conditions.presence_of_element_located((",
                "                    by_value(by_module, locator[\"by\"]),",
                "                    locator[\"value\"],",
                "                ))",
                "            )",
                "        return {\"status\": \"ok\", \"checked_locators\": [locator[\"name\"] for locator in LOCATORS]}",
                "    except Exception as exc:",
                "        screenshot = screenshot_dir / \"failure.png\"",
                "        driver.save_screenshot(str(screenshot))",
                "        return {\"status\": \"failed\", \"error\": str(exc), \"screenshot\": str(screenshot)}",
                "    finally:",
                "        driver.quit()",
                "",
                "",
                "def main(argv: list[str] | None = None) -> int:",
                "    parser = build_parser()",
                "    args = parser.parse_args(argv)",
                "    logging.basicConfig(level=logging.INFO, format=\"%(levelname)s %(message)s\")",
                "    logger = logging.getLogger(\"selenium-automation\")",
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
        reasons = self.markdown_list(spec["selenium_reasons"], fallback="No Selenium reason provided.")
        selectors = self.markdown_list([selector["name"] for selector in spec["selectors"]], fallback="No selectors.")
        gates = self.markdown_list(spec["quality_gates"], fallback="Review dry-run and screenshots.")
        return "\n".join(
            [
                f"# {spec['automation_name']}",
                "",
                spec["purpose"],
                "",
                "## Why Selenium",
                "",
                reasons,
                "",
                "## Usage",
                "",
                "```bash",
                "python selenium_automation.py --dry-run",
                "python selenium_automation.py --execute --confirm --headless",
                "```",
                "",
                "## Selectors",
                "",
                selectors,
                "",
                "## Quality Gates",
                "",
                gates,
                "",
                "## Guardrails",
                "",
                "- Use explicit waits.",
                "- Capture screenshot on failure.",
                "- Do not hardcode credentials.",
                "- Prefer Playwright when Selenium/WebDriver is not required.",
                "",
            ]
        )

    def render_selenium_test(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "import json",
                "import subprocess",
                "import sys",
                "from pathlib import Path",
                "",
                "",
                "def test_selenium_automation_dry_run_returns_plan_without_browser():",
                "    script = Path(__file__).resolve().parents[1] / \"selenium_automation.py\"",
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
            "inputs": {"required": [], "optional": ["dry-run", "execute", "confirm", "headless", "browser"]},
            "outputs": {"artifacts": ["selenium-result.json", "failure.png"]},
            "write_policy": self.capability_write_policy(spec["side_effects"]),
        }
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)

    def render_capability_workflow(self, spec: dict[str, Any], *, capability_id: str) -> str:
        return "\n".join(
            [
                "# Workflow",
                "",
                f"1. Executar `{capability_id}` em dry-run por padrao.",
                "2. Revisar plano, browser, target e locators.",
                "3. Executar com `--execute --confirm --confirm-execute` apenas apos revisar riscos.",
                "4. Retornar JSON e screenshot em falha.",
                "",
            ]
        )

    def render_capability_decision_rules(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "# Decision Rules",
                "",
                f"- Side effects classificados como `{spec['side_effects']}`.",
                "- Usar waits explicitos.",
                "- Escrita ou submissao exige confirmacao.",
                "- Playwright deve ser preferido quando Selenium nao for requisito.",
                "",
            ]
        )

    def normalize_selector(self, value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            return {"name": "invalid", "by": "css", "value": str(value)}
        selector = {
            "name": str(value.get("name") or "selector").strip(),
            "by": str(value.get("by") or "css").strip(),
            "value": str(value.get("value") or "").strip(),
        }
        if selector["by"] not in SELECTOR_BY_MAP:
            selector["by"] = "css"
        return selector

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
            "read-only": ["Dry-run shows target and locators without opening browser."],
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
        if spec["auth_strategy"] == "env":
            questions.append("Quais env vars de credencial serao referenciadas sem expor valores?")
        if spec["side_effects"] != "read-only":
            questions.append("Qual ambiente seguro confirma que a automacao nao afetara dados reais?")
        if not spec["remote_url_env"]:
            questions.append("Ha Selenium Grid ou browser remoto, ou a execucao sera local?")
        return questions

    def question_for_missing_field(self, field: str) -> str:
        questions = {
            "automation_name": "Qual sera o nome da automacao Selenium?",
            "purpose": "Qual tarefa web a automacao deve resolver?",
            "target_url_or_description": "Qual URL ou descricao do alvo Selenium?",
            "browser": "Qual browser WebDriver sera usado?",
            "selectors": "Quais seletores estaveis serao usados?",
            "steps": "Quais passos a automacao executa?",
            "auth_strategy": "Qual estrategia de autenticacao sera usada?",
            "side_effects": "Qual classificacao de side effects se aplica?",
            "selenium_reasons": "Qual motivo tecnico justifica Selenium em vez de Playwright?",
        }
        return questions.get(field, f"Informe o campo obrigatorio {field}.")

    def markdown_list(self, values: list[str], *, fallback: str) -> str:
        if not values:
            return f"- {fallback}"
        return "\n".join(f"- {value}" for value in values)

    def slugify(self, value: str) -> str:
        slug = SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
        return slug or "selenium-automation"

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
