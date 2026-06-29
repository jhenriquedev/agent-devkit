"""Repository for local, read-only Supabase project analysis."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any


EXPOSED_SCHEMAS = {"public"}
SECRET_KEY_PATTERN = re.compile(
    r"(SUPABASE_ACCESS_TOKEN|SUPABASE_DB_URL|SUPABASE_SERVICE_ROLE_KEY|SUPABASE_ANON_KEY|SERVICE_ROLE_KEY|service_role|jwt_secret|anon_key)",
    re.IGNORECASE,
)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(SUPABASE_ACCESS_TOKEN|SUPABASE_DB_URL|SUPABASE_SERVICE_ROLE_KEY|SUPABASE_ANON_KEY|SERVICE_ROLE_KEY|JWT_SECRET|service_role|jwt_secret|anon_key)\b\s*[:=]\s*['\"]?([^'\"\n]+)"
)
POSTGRES_URL_PATTERN = re.compile(r"postgres(?:ql)?://[^\s'\"<>]+", re.IGNORECASE)
CREATE_TABLE_PATTERN = re.compile(
    r"create\s+table\s+(?:if\s+not\s+exists\s+)?(?P<name>(?:\"?\w+\"?\.)?\"?\w+\"?)",
    re.IGNORECASE,
)
ENABLE_RLS_PATTERN = re.compile(
    r"alter\s+table\s+(?:only\s+)?(?P<name>(?:\"?\w+\"?\.)?\"?\w+\"?)\s+enable\s+row\s+level\s+security",
    re.IGNORECASE,
)
POLICY_PATTERN = re.compile(
    r"create\s+policy\s+(?P<name>.+?)\s+on\s+(?P<table>(?:\"?\w+\"?\.)?\"?\w+\"?)(?P<body>.*?);",
    re.IGNORECASE | re.DOTALL,
)
CREATE_VIEW_PATTERN = re.compile(
    r"create\s+(?:or\s+replace\s+)?view\s+(?P<name>(?:\"?\w+\"?\.)?\"?\w+\"?)(?P<body>.*?);",
    re.IGNORECASE | re.DOTALL,
)
SECURITY_DEFINER_PATTERN = re.compile(
    r"create\s+(?:or\s+replace\s+)?function\s+(?P<name>(?:\"?\w+\"?\.)?\"?\w+\"?)\s*\(.*?security\s+definer",
    re.IGNORECASE | re.DOTALL,
)
DESTRUCTIVE_DDL_PATTERN = re.compile(
    r"\b(drop\s+table|truncate\s+table|alter\s+table\s+.+?\s+drop\s+column|drop\s+schema)\b",
    re.IGNORECASE | re.DOTALL,
)
GRANT_PUBLIC_PATTERN = re.compile(
    r"grant\s+.+?\s+on\s+.+?\s+to\s+(anon|authenticated|public)\b",
    re.IGNORECASE | re.DOTALL,
)


class SupabaseProjectError(RuntimeError):
    """Raised when the project cannot be inspected."""


class SqlFile:
    def __init__(self, *, path: Path, relative_path: str, text: str) -> None:
        self.path = path
        self.relative_path = relative_path
        self.text = text


class SupabaseProjectRepository:
    def inspect_supabase_project(
        self,
        *,
        project_path: Path,
        include_cli_status: bool = False,
    ) -> dict[str, Any]:
        project_root = self.resolve_project(project_path)
        context = self.collect_context(project_root, include_cli_status=include_cli_status)
        return {
            "kind": "supabase-project-inspection",
            "status": "ok",
            "project_path": str(project_root),
            "write_policy": "read_only",
            "context": context,
            "secret_exposure": self.secret_inventory(project_root),
        }

    def audit_rls_policies(self, *, project_path: Path) -> dict[str, Any]:
        project_root = self.resolve_project(project_path)
        sql_files = self.sql_files(project_root)
        findings = self.find_rls_findings(sql_files)
        return self.audit_payload("supabase-rls-audit", project_root, findings)

    def audit_auth_security(self, *, project_path: Path) -> dict[str, Any]:
        project_root = self.resolve_project(project_path)
        findings = self.find_auth_findings(project_root, self.sql_files(project_root))
        return self.audit_payload("supabase-auth-audit", project_root, findings)

    def audit_storage_policies(self, *, project_path: Path) -> dict[str, Any]:
        project_root = self.resolve_project(project_path)
        findings = self.find_storage_findings(self.sql_files(project_root))
        return self.audit_payload("supabase-storage-audit", project_root, findings)

    def review_migrations(self, *, project_path: Path) -> dict[str, Any]:
        project_root = self.resolve_project(project_path)
        findings = self.find_migration_findings(self.sql_files(project_root))
        return self.audit_payload("supabase-migration-review", project_root, findings)

    def generate_supabase_report(self, *, project_path: Path) -> dict[str, Any]:
        project_root = self.resolve_project(project_path)
        findings = self.all_findings(project_root)
        severity_counts = Counter(finding["severity"] for finding in findings)
        category_counts = Counter(finding["category"] for finding in findings)
        return {
            "kind": "supabase-report",
            "status": "ok",
            "project_path": str(project_root),
            "write_policy": "output_only",
            "facts": self.collect_context(project_root, include_cli_status=False),
            "summary": {
                "findings": len(findings),
                "by_severity": dict(sorted(severity_counts.items())),
                "by_category": dict(sorted(category_counts.items())),
            },
            "findings": findings,
            "recommendations": self.recommendations(findings),
        }

    def plan_supabase_fix(self, *, project_path: Path) -> dict[str, Any]:
        project_root = self.resolve_project(project_path)
        findings = self.all_findings(project_root)
        actions = [self.fix_action_for(finding) for finding in findings]
        actions = [action for action in actions if action]
        return {
            "kind": "supabase-fix-plan",
            "status": "ok",
            "project_path": str(project_root),
            "write_policy": "dry_run",
            "apply_real": False,
            "findings_count": len(findings),
            "actions": actions,
            "blocked_actions": ["execute_sql", "apply_migration", "supabase db push", "supabase functions deploy"],
        }

    def resolve_project(self, project_path: Path) -> Path:
        root = project_path.expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise SupabaseProjectError(f"project path not found: {root}")
        return root

    def collect_context(self, project_root: Path, *, include_cli_status: bool) -> dict[str, Any]:
        supabase_dir = project_root / "supabase"
        migrations_dir = supabase_dir / "migrations"
        functions_dir = supabase_dir / "functions"
        config_path = supabase_dir / "config.toml"
        config = self.read_config(config_path)
        return {
            "has_supabase_dir": supabase_dir.exists(),
            "config_path": str(config_path.relative_to(project_root)) if config_path.exists() else None,
            "project_ref": self.redact_value(os.environ.get("SUPABASE_PROJECT_REF") or self.project_ref_from_config(config)),
            "migrations_count": len(list(migrations_dir.glob("*.sql"))) if migrations_dir.exists() else 0,
            "edge_functions": self.edge_functions(functions_dir),
            "seed_present": (supabase_dir / "seed.sql").exists(),
            "config": self.safe_config_summary(config),
            "cli_status": self.cli_status() if include_cli_status else {"checked": False},
            "mcp": self.mcp_status(project_root),
        }

    def read_config(self, config_path: Path) -> dict[str, Any]:
        if not config_path.exists():
            return {}
        try:
            return tomllib.loads(config_path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError) as exc:
            return {"_error": str(exc)}

    def project_ref_from_config(self, config: dict[str, Any]) -> str | None:
        value = config.get("project_id") or config.get("project_ref") if isinstance(config, dict) else None
        return str(value) if value else None

    def safe_config_summary(self, config: dict[str, Any]) -> dict[str, Any]:
        if not config:
            return {}
        return {
            key: self.safe_config_value(value)
            for key, value in config.items()
            if not SECRET_KEY_PATTERN.search(str(key))
        }

    def safe_config_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.redact_value(value)
        if isinstance(value, dict):
            return self.safe_config_summary(value)
        if isinstance(value, list):
            return [self.safe_config_value(item) for item in value]
        return value

    def edge_functions(self, functions_dir: Path) -> list[str]:
        if not functions_dir.exists():
            return []
        return sorted(path.name for path in functions_dir.iterdir() if path.is_dir())

    def mcp_status(self, project_root: Path) -> dict[str, Any]:
        mcp_json = project_root / ".mcp.json"
        return {
            "config_present": mcp_json.exists(),
            "supabase_server_declared": "supabase" in self.redact_text(mcp_json.read_text(encoding="utf-8")) if mcp_json.exists() else False,
            "oauth_required": True,
        }

    def cli_status(self) -> dict[str, Any]:
        executable = shutil.which("supabase")
        if not executable:
            return {"checked": True, "available": False}
        return {
            "checked": True,
            "available": True,
            "version": self.safe_command(["supabase", "--version"]),
            "help_available": self.safe_command(["supabase", "--help"], max_chars=500)["returncode"] == 0,
            "db_help_available": self.safe_command(["supabase", "db", "--help"], max_chars=500)["returncode"] == 0,
        }

    def safe_command(self, command: list[str], *, max_chars: int = 2000) -> dict[str, Any]:
        try:
            result = subprocess.run(
                command,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"returncode": 1, "stdout": "", "stderr": self.redact_text(str(exc))}
        return {
            "returncode": result.returncode,
            "stdout": self.redact_text(result.stdout[:max_chars]),
            "stderr": self.redact_text(result.stderr[:max_chars]),
        }

    def sql_files(self, project_root: Path) -> list[SqlFile]:
        supabase_dir = project_root / "supabase"
        paths: list[Path] = []
        migrations_dir = supabase_dir / "migrations"
        if migrations_dir.exists():
            paths.extend(sorted(migrations_dir.glob("*.sql")))
        seed = supabase_dir / "seed.sql"
        if seed.exists():
            paths.append(seed)
        sql_files: list[SqlFile] = []
        for path in paths:
            text = path.read_text(encoding="utf-8", errors="replace")
            sql_files.append(SqlFile(path=path, relative_path=str(path.relative_to(project_root)), text=text))
        return sql_files

    def all_findings(self, project_root: Path) -> list[dict[str, Any]]:
        sql_files = self.sql_files(project_root)
        findings = [
            *self.find_rls_findings(sql_files),
            *self.find_auth_findings(project_root, sql_files),
            *self.find_storage_findings(sql_files),
            *self.find_migration_findings(sql_files),
        ]
        return self.dedupe_findings(findings)

    def find_rls_findings(self, sql_files: list[SqlFile]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        tables = self.created_tables(sql_files)
        rls_enabled = self.rls_enabled_tables(sql_files)
        for table, source in tables.items():
            if self.schema_for(table) in EXPOSED_SCHEMAS and table not in rls_enabled:
                findings.append(self.finding(
                    "high",
                    "rls",
                    "exposed_table_without_rls",
                    source,
                    f"Table `{table}` is in an exposed schema without ENABLE ROW LEVEL SECURITY.",
                    "Tables in exposed schemas can be reachable through the Data API.",
                    f"Enable RLS on `{table}` and add policies matching the access model.",
                    suggested_sql=f"alter table {table} enable row level security;",
                ))
        for sql_file in sql_files:
            for policy in POLICY_PATTERN.finditer(sql_file.text):
                body = policy.group("body")
                table = self.normalize_identifier(policy.group("table"))
                if "auth.role()" in body.lower():
                    findings.append(self.finding(
                        "medium",
                        "rls",
                        "deprecated_auth_role",
                        sql_file,
                        self.line_for(sql_file.text, policy.start()),
                        "`auth.role()` is used in an RLS policy.",
                        "Supabase recommends using the policy TO clause instead.",
                        "Replace auth.role() checks with explicit TO anon/authenticated and ownership predicates.",
                    ))
                if re.search(r"\bto\s+authenticated\b", body, re.IGNORECASE) and not self.has_ownership_predicate(body):
                    findings.append(self.finding(
                        "high",
                        "rls",
                        "authenticated_without_ownership",
                        sql_file,
                        self.line_for(sql_file.text, policy.start()),
                        f"Policy on `{table}` targets authenticated without an ownership predicate.",
                        "Authentication without row ownership can create BOLA/IDOR exposure.",
                        "Add a USING predicate based on `(select auth.uid())` and tenant/user ownership.",
                    ))
                if re.search(r"\bfor\s+update\b", body, re.IGNORECASE) and "with check" not in body.lower():
                    findings.append(self.finding(
                        "high",
                        "rls",
                        "update_policy_without_with_check",
                        sql_file,
                        self.line_for(sql_file.text, policy.start()),
                        f"UPDATE policy on `{table}` does not include WITH CHECK.",
                        "Users may be able to update ownership columns into unauthorized values.",
                        "Add a WITH CHECK predicate matching the USING ownership predicate.",
                    ))
        return findings

    def find_auth_findings(self, project_root: Path, sql_files: list[SqlFile]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        searchable_files = [*sql_files, *self.edge_source_files(project_root)]
        for source in searchable_files:
            lower = source.text.lower()
            if "raw_user_meta_data" in lower or "user_metadata" in lower:
                findings.append(self.finding(
                    "high",
                    "auth",
                    "user_metadata_authorization",
                    source,
                    self.line_for(source.text, min(pos for pos in [lower.find("raw_user_meta_data"), lower.find("user_metadata")] if pos >= 0)),
                    "User-editable metadata appears in authorization-sensitive code.",
                    "Supabase user metadata can be edited by the user and is unsafe for authorization.",
                    "Move authorization attributes to app_metadata/raw_app_meta_data or server-side tables.",
                ))
            if re.search(r"service[_-]?role|SUPABASE_SERVICE_ROLE_KEY", source.text, re.IGNORECASE):
                findings.append(self.finding(
                    "critical",
                    "auth",
                    "service_role_reference",
                    source,
                    self.line_for(source.text, re.search(r"service[_-]?role|SUPABASE_SERVICE_ROLE_KEY", source.text, re.IGNORECASE).start()),
                    "Service role key/reference appears in local project code or SQL.",
                    "Service role bypasses RLS and must never be exposed to public clients.",
                    "Move service role use to trusted server-only environments and verify it is not bundled.",
                ))
        for env_path in self.env_files(project_root):
            text = env_path.read_text(encoding="utf-8", errors="replace")
            if SECRET_KEY_PATTERN.search(text):
                findings.append({
                    "severity": "medium",
                    "code": "local_env_secret_present",
                    "category": "auth",
                    "file": str(env_path.relative_to(project_root)),
                    "line": 1,
                    "evidence": "Local env file contains Supabase secret markers; values redacted.",
                    "risk": "Accidental commit or log exposure can leak credentials.",
                    "recommendation": "Ensure env files are ignored and never included in generated artifacts.",
                    "suggested_sql": None,
                })
        return findings

    def find_storage_findings(self, sql_files: list[SqlFile]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        storage_policies = []
        for sql_file in sql_files:
            for policy in POLICY_PATTERN.finditer(sql_file.text):
                table = self.normalize_identifier(policy.group("table"))
                if table == "storage.objects":
                    body = policy.group("body")
                    storage_policies.append(body.lower())
                    if re.search(r"\bto\s+(anon|public)\b", body, re.IGNORECASE) or re.search(r"using\s*\(\s*true\s*\)", body, re.IGNORECASE):
                        findings.append(self.finding(
                            "high",
                            "storage",
                            "storage_public_policy",
                            sql_file,
                            self.line_for(sql_file.text, policy.start()),
                            "Storage policy appears broadly public.",
                            "Public Storage access can expose private files or tenant data.",
                            "Restrict object paths by user/org and avoid `USING (true)` unless the bucket is intentionally public.",
                        ))
        combined = "\n".join(storage_policies)
        if "upsert" in combined and not all(token in combined for token in ("for select", "for insert", "for update")):
            findings.append({
                "severity": "medium",
                "code": "storage_upsert_missing_policy_set",
                "category": "storage",
                "file": None,
                "line": None,
                "evidence": "Storage upsert is mentioned but SELECT/INSERT/UPDATE policy set is incomplete.",
                "risk": "Supabase Storage upsert requires INSERT, SELECT and UPDATE permissions.",
                "recommendation": "Define the full policy set for upload and replacement paths.",
                "suggested_sql": None,
            })
        return findings

    def find_migration_findings(self, sql_files: list[SqlFile]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for sql_file in sql_files:
            for match in DESTRUCTIVE_DDL_PATTERN.finditer(sql_file.text):
                findings.append(self.finding(
                    "high",
                    "migration",
                    "destructive_ddl",
                    sql_file,
                    self.line_for(sql_file.text, match.start()),
                    self.redact_text(match.group(0)),
                    "Destructive DDL can cause data loss or downtime.",
                    "Require rollback, backup, lock/timeout strategy and explicit confirmation before applying.",
                ))
            for match in SECURITY_DEFINER_PATTERN.finditer(sql_file.text):
                name = self.normalize_identifier(match.group("name"))
                severity = "critical" if self.schema_for(name) in EXPOSED_SCHEMAS else "high"
                findings.append(self.finding(
                    severity,
                    "migration",
                    "security_definer_function",
                    sql_file,
                    self.line_for(sql_file.text, match.start()),
                    f"`SECURITY DEFINER` function `{name}` detected.",
                    "SECURITY DEFINER bypasses caller privileges and can bypass RLS.",
                    "Prefer SECURITY INVOKER; if needed, keep in non-exposed schema with explicit auth.uid() checks and grants.",
                ))
            for match in CREATE_VIEW_PATTERN.finditer(sql_file.text):
                body = match.group("body")
                if "security_invoker" not in body.lower():
                    name = self.normalize_identifier(match.group("name"))
                    findings.append(self.finding(
                        "medium",
                        "migration",
                        "view_without_security_invoker",
                        sql_file,
                        self.line_for(sql_file.text, match.start()),
                        f"View `{name}` is created without `security_invoker`.",
                        "Views can bypass RLS by default depending on ownership/Postgres version.",
                        "Use `WITH (security_invoker = true)` where supported or keep view outside exposed schemas.",
                    ))
            for match in GRANT_PUBLIC_PATTERN.finditer(sql_file.text):
                findings.append(self.finding(
                    "medium",
                    "migration",
                    "broad_grant_to_public_roles",
                    sql_file,
                    self.line_for(sql_file.text, match.start()),
                    self.redact_text(match.group(0)),
                    "Broad grants to anon/authenticated/public can expose Data API surfaces.",
                    "Pair grants with RLS and least-privilege access.",
                ))
        return findings

    def edge_source_files(self, project_root: Path) -> list[SqlFile]:
        functions_dir = project_root / "supabase" / "functions"
        if not functions_dir.exists():
            return []
        files = []
        for path in sorted(functions_dir.rglob("*")):
            if path.suffix.lower() not in {".ts", ".js", ".tsx", ".jsx"} or not path.is_file():
                continue
            files.append(SqlFile(path=path, relative_path=str(path.relative_to(project_root)), text=path.read_text(encoding="utf-8", errors="replace")))
        return files

    def env_files(self, project_root: Path) -> list[Path]:
        return [path for path in sorted(project_root.glob(".env*")) if path.is_file()]

    def created_tables(self, sql_files: list[SqlFile]) -> dict[str, SqlFile]:
        tables: dict[str, SqlFile] = {}
        for sql_file in sql_files:
            for match in CREATE_TABLE_PATTERN.finditer(sql_file.text):
                name = self.normalize_identifier(match.group("name"))
                if name.startswith("storage.") or name.startswith("auth."):
                    continue
                tables[name] = sql_file
        return tables

    def rls_enabled_tables(self, sql_files: list[SqlFile]) -> set[str]:
        enabled: set[str] = set()
        for sql_file in sql_files:
            for match in ENABLE_RLS_PATTERN.finditer(sql_file.text):
                enabled.add(self.normalize_identifier(match.group("name")))
        return enabled

    def normalize_identifier(self, value: str) -> str:
        cleaned = value.replace('"', "").strip().lower()
        if "." not in cleaned:
            return f"public.{cleaned}"
        return cleaned

    def schema_for(self, identifier: str) -> str:
        return identifier.split(".", 1)[0] if "." in identifier else "public"

    def has_ownership_predicate(self, value: str) -> bool:
        lower = value.lower()
        return "auth.uid()" in lower or "(select auth.uid())" in lower or "owner_id" in lower or "user_id" in lower or "tenant_id" in lower or "organization_id" in lower

    def finding(
        self,
        severity: str,
        category: str,
        code: str,
        source: SqlFile,
        line_or_evidence: int | str,
        evidence_or_risk: str,
        risk_or_recommendation: str,
        recommendation: str | None = None,
        *,
        suggested_sql: str | None = None,
    ) -> dict[str, Any]:
        if isinstance(line_or_evidence, int):
            line = line_or_evidence
            evidence = evidence_or_risk
            risk = risk_or_recommendation
            rec = recommendation or ""
        else:
            line = 1
            evidence = line_or_evidence
            risk = evidence_or_risk
            rec = risk_or_recommendation
        return {
            "severity": severity,
            "code": code,
            "category": category,
            "file": source.relative_path,
            "line": line,
            "evidence": self.redact_text(evidence),
            "risk": risk,
            "recommendation": rec,
            "suggested_sql": suggested_sql,
        }

    def audit_payload(self, kind: str, project_root: Path, findings: list[dict[str, Any]]) -> dict[str, Any]:
        severity_counts = Counter(finding["severity"] for finding in findings)
        return {
            "kind": kind,
            "status": "ok",
            "project_path": str(project_root),
            "write_policy": "read_only",
            "findings_count": len(findings),
            "by_severity": dict(sorted(severity_counts.items())),
            "findings": self.dedupe_findings(findings),
        }

    def recommendations(self, findings: list[dict[str, Any]]) -> list[str]:
        by_code = {finding["code"]: finding["recommendation"] for finding in findings}
        return [by_code[code] for code in sorted(by_code)]

    def fix_action_for(self, finding: dict[str, Any]) -> dict[str, Any] | None:
        return {
            "finding_code": finding["code"],
            "severity": finding["severity"],
            "file": finding.get("file"),
            "line": finding.get("line"),
            "recommendation": finding["recommendation"],
            "suggested_sql": finding.get("suggested_sql"),
            "apply_real": False,
        }

    def secret_inventory(self, project_root: Path) -> dict[str, Any]:
        markers = []
        supabase_paths = list((project_root / "supabase").rglob("*")) if (project_root / "supabase").exists() else []
        for path in [*self.env_files(project_root), *supabase_paths]:
            if not path.is_file() or path.stat().st_size > 1024 * 1024:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if SECRET_KEY_PATTERN.search(text) or POSTGRES_URL_PATTERN.search(text):
                markers.append(str(path.relative_to(project_root)))
        return {"files_with_secret_markers": sorted(set(markers)), "values_redacted": True}

    def redact_value(self, value: Any) -> Any:
        if value is None:
            return None
        return self.redact_text(str(value))

    def redact_text(self, text: str) -> str:
        redacted = POSTGRES_URL_PATTERN.sub("<redacted-postgres-url>", text)
        redacted = SECRET_ASSIGNMENT_PATTERN.sub(lambda match: f"{match.group(1)}=<redacted>", redacted)
        return redacted

    def line_for(self, text: str, index: int) -> int:
        return text.count("\n", 0, max(index, 0)) + 1

    def dedupe_findings(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[Any, ...]] = set()
        unique = []
        for finding in findings:
            key = (finding.get("code"), finding.get("file"), finding.get("line"), finding.get("evidence"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(finding)
        return unique
