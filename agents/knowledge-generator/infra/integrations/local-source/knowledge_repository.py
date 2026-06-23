#!/usr/bin/env python3
"""Local source adapters and knowledge writer for knowledge-generator."""

from __future__ import annotations

import csv
import html
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


class KnowledgeGeneratorError(RuntimeError):
    """Raised for user-facing knowledge generation errors."""


# ---------------------------------------------------------------------------
# Policies — loaded from knowledge/policies.yaml (source of truth).
# Falls back to hardcoded defaults when the YAML is not available so that
# the module remains usable outside the agent tree (e.g. during tests).
# ---------------------------------------------------------------------------

_POLICIES_PATH = Path(__file__).resolve().parents[3] / "knowledge" / "policies.yaml"


def _load_policies() -> dict[str, Any]:
    """Load policies.yaml using stdlib only (no PyYAML dependency required)."""
    try:
        import yaml  # type: ignore

        with _POLICIES_PATH.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception:
        pass
    # Minimal hand-rolled parser sufficient for the simple key: value / list structure
    try:
        text = _POLICIES_PATH.read_text(encoding="utf-8")
        result: dict[str, Any] = {}
        current_section: str | None = None
        current_list: list[str] | None = None
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if indent == 0 and stripped.endswith(":"):
                current_section = stripped[:-1]
                result[current_section] = {}
                current_list = None
            elif indent == 2 and current_section and ":" in stripped:
                key, _, val = stripped.partition(":")
                val = val.strip()
                if val == "":
                    current_list = []
                    result[current_section][key.strip()] = current_list
                elif val.lower() in ("true", "false"):
                    result[current_section][key.strip()] = val.lower() == "true"
                elif val.isdigit():
                    result[current_section][key.strip()] = int(val)
                else:
                    result[current_section][key.strip()] = val
                    current_list = None
            elif indent == 4 and current_list is not None and stripped.startswith("- "):
                current_list.append(stripped[2:].strip())
        return result
    except Exception:
        return {}


_POLICIES: dict[str, Any] = _load_policies()


def _policy_ignored_dirs() -> set[str]:
    dirs = (
        (_POLICIES.get("source_handling") or {}).get("ignore_common_generated_directories") or []
    )
    base = {
        ".git", ".hg", ".svn", ".next", ".serverless", ".venv",
        "__pycache__", "bin", "build", "coverage", "dist",
        "node_modules", "obj", "target", "vendor",
    }
    if dirs:
        return set(dirs)
    return base


def _policy_max_bytes() -> int:
    val = ((_POLICIES.get("source_handling") or {}).get("max_default_file_size_bytes"))
    if isinstance(val, int) and val > 0:
        return val
    return 500_000


IGNORED_DIRS: set[str] = _policy_ignored_dirs()
MAX_TEXT_BYTES: int = _policy_max_bytes()

LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".cs": "csharp",
    ".csproj": "csharp-project",
    ".sln": "csharp-solution",
    ".dart": "dart",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".java": "java",
    ".kt": "kotlin",
    ".go": "go",
    ".php": "php",
    ".rb": "ruby",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
}

DOCUMENT_SUFFIXES = {
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".pdf",
    ".docx",
    ".pptx",
}

DATA_SUFFIXES = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".wsdl",
    ".csv",
    ".xlsx",
}

CONFIG_NAMES = {
    "package.json",
    "pubspec.yaml",
    "requirements.txt",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
    "Dockerfile",
    "docker-compose.yml",
    ".env.example",
}

SECRET_PATTERNS = [
    (r"(?i)(authorization\s*:\s*bearer\s+)[^\s,;]+", r"\1{{token}}"),
    (r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+", r"\1{{api_key}}"),
    (r"(?i)(password\s*[:=]\s*)[^\s,;]+", r"\1{{password}}"),
    (r"(?i)(secret\s*[:=]\s*)[^\s,;]+", r"\1{{secret}}"),
    (r"(?i)(connectionstring\s*[:=]\s*)[^\n]+", r"\1{{connection_string}}"),
    (r"(?i)(connection[_-]?string\s*[:=]\s*)[^\n]+", r"\1{{connection_string}}"),
    # cookies
    (r"(?i)(set-cookie\s*:\s*)[^\n]+", r"\1{{cookie}}"),
    (r"(?i)(cookie\s*[:=]\s*)[^\s,;]+", r"\1{{cookie}}"),
    # private keys / certificates (PEM blocks)
    (r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[A-Za-z0-9+/=\r\n]+-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "{{private_key}}"),
    (r"-----BEGIN CERTIFICATE-----[A-Za-z0-9+/=\r\n]+-----END CERTIFICATE-----", "{{certificate}}"),
]

PROFILES: dict[str, dict[str, Any]] = {
    "code-project": {
        "name": "Code Project",
        "description": "Projetos de codigo backend, servicos, jobs, CLIs e integracoes.",
        "source_kinds": ["code", "configuration", "documentation", "data"],
        "required_artifacts": [
            "project.json",
            "source-index.json",
            "code-inventory.json",
            "coverage-assessment.md",
            "hardening/initial-gaps.json",
        ],
    },
    "frontend-app": {
        "name": "Frontend App",
        "description": "Apps Flutter/Dart, HTML, CSS e frontends com telas, componentes e assets.",
        "source_kinds": ["code", "frontend", "configuration", "documentation"],
        "required_artifacts": [
            "project.json",
            "source-index.json",
            "code-inventory.json",
            "frontend-inventory.json",
            "coverage-assessment.md",
            "hardening/initial-gaps.json",
        ],
    },
    "documentation-set": {
        "name": "Documentation Set",
        "description": "Manuais, PDFs, Markdown, Word, wikis e documentos de referencia.",
        "source_kinds": ["documentation", "text"],
        "required_artifacts": [
            "project.json",
            "source-index.json",
            "document-map.json",
            "coverage-assessment.md",
            "hardening/initial-gaps.json",
        ],
    },
    "business-domain": {
        "name": "Business Domain",
        "description": "Processos, atores, regras de negocio, decisoes e jornadas.",
        "source_kinds": ["documentation", "data", "process"],
        "required_artifacts": [
            "project.json",
            "source-index.json",
            "domain.json",
            "coverage-assessment.md",
            "hardening/initial-gaps.json",
        ],
    },
    "integration-docs": {
        "name": "Integration Docs",
        "description": "Contratos REST, SOAP, SFTP, MCP, payloads, autenticacao e erros.",
        "source_kinds": ["documentation", "data", "api"],
        "required_artifacts": [
            "project.json",
            "source-index.json",
            "integration.json",
            "coverage-assessment.md",
            "hardening/initial-gaps.json",
        ],
    },
    "support-operations": {
        "name": "Support Operations",
        "description": "Runbooks, sintomas, evidencias, playbooks e troubleshooting.",
        "source_kinds": ["documentation", "operations"],
        "required_artifacts": [
            "project.json",
            "source-index.json",
            "operations.json",
            "coverage-assessment.md",
            "hardening/initial-gaps.json",
        ],
    },
    "data-domain": {
        "name": "Data Domain",
        "description": "Arquivos de dados, schemas, tabelas, entidades, metricas e linhagem.",
        "source_kinds": ["data", "configuration"],
        "required_artifacts": [
            "project.json",
            "source-index.json",
            "data-inventory.json",
            "coverage-assessment.md",
            "hardening/initial-gaps.json",
        ],
    },
    "mixed-knowledge": {
        "name": "Mixed Knowledge",
        "description": "Conjuntos heterogeneos com documentos, codigo, dados e configuracoes.",
        "source_kinds": ["code", "documentation", "data", "configuration"],
        "required_artifacts": [
            "project.json",
            "source-index.json",
            "coverage-assessment.md",
            "hardening/initial-gaps.json",
        ],
    },
    "freeform": {
        "name": "Freeform",
        "description": "Fallback para fontes pequenas ou pouco estruturadas.",
        "source_kinds": ["text", "unknown"],
        "required_artifacts": [
            "project.json",
            "source-index.json",
            "coverage-assessment.md",
            "hardening/initial-gaps.json",
        ],
    },
}


@dataclass(frozen=True)
class SourceFile:
    path: Path
    relative_path: Path
    suffix: str
    size: int
    content_kind: str
    language: str | None
    text: str
    ignored_reason: str | None = None

    def as_index_item(self, source_id: str) -> dict[str, Any]:
        return {
            "id": source_id,
            "path": portable(self.relative_path),
            "source_type": self.content_kind,
            "language": self.language,
            "size_bytes": self.size,
            "preview": compact(self.text)[:400],
        }


class KnowledgeRepository:
    """Inspect local sources and generate profile-driven knowledge."""

    def list_profiles(self) -> dict[str, Any]:
        return {
            "profiles": [
                {
                    "id": profile_id,
                    "name": profile["name"],
                    "description": profile["description"],
                    "source_kinds": profile["source_kinds"],
                    "required_artifacts": profile["required_artifacts"],
                }
                for profile_id, profile in PROFILES.items()
            ]
        }

    def inspect_source(
        self,
        *,
        source: str,
        profile: str = "auto",
        project_id: str | None = None,
    ) -> dict[str, Any]:
        source_path = Path(source).expanduser().resolve()
        if not source_path.exists():
            raise KnowledgeGeneratorError(f"source not found: {source_path}")

        files, ignored = collect_files(source_path)
        source_files = [load_source_file(source_path, path) for path in files]
        languages = sorted({item.language for item in source_files if item.language})
        content_kinds = sorted({item.content_kind for item in source_files})
        recommended_profile = resolve_profile(source_files, profile)
        signals = detect_signals(source_files)

        return {
            "source": {
                "path": str(source_path),
                "kind": "directory" if source_path.is_dir() else "file",
                "file_count": len(source_files),
                "ignored_count": len(ignored),
                "languages": languages,
                "content_kinds": content_kinds,
                "signals": signals,
                "files": [
                    item.as_index_item(f"source-{index}")
                    for index, item in enumerate(source_files, start=1)
                ],
                "ignored": ignored,
            },
            "requested_profile": profile,
            "recommended_profile": recommended_profile,
            "project_id": project_id or slugify(source_path.stem or source_path.name),
        }

    def generate_knowledge(
        self,
        *,
        source: str,
        output_dir: str | None = None,
        profile: str = "auto",
        project_id: str | None = None,
        yes_create_dir: bool = False,
        yes_overwrite: bool = False,
    ) -> dict[str, Any]:
        source_path = Path(source).expanduser().resolve()
        inspect = self.inspect_source(source=str(source_path), profile=profile, project_id=project_id)
        resolved_profile = inspect["recommended_profile"]
        resolved_project_id = project_id or inspect["project_id"]
        output_path = resolve_output_dir(output_dir, source_path)
        ensure_output_dir(output_path, yes_create_dir)

        files, _ignored = collect_files(source_path)
        source_files = [load_source_file(source_path, path) for path in files]
        documents = build_documents(
            source_path=source_path,
            source_files=source_files,
            inspect=inspect,
            profile=resolved_profile,
            project_id=resolved_project_id,
        )
        write_documents(output_path, documents, yes_overwrite)
        validation = self.validate_knowledge(knowledge_dir=str(output_path))

        return {
            "output_dir": str(output_path),
            "profile": resolved_profile,
            "project_id": resolved_project_id,
            "artifacts": sorted(documents),
            "validation": validation,
        }

    def validate_knowledge(self, *, knowledge_dir: str) -> dict[str, Any]:
        path = Path(knowledge_dir).expanduser().resolve()
        errors: list[str] = []
        warnings: list[str] = []
        if not path.exists() or not path.is_dir():
            return {"valid": False, "errors": [f"knowledge directory not found: {path}"], "warnings": []}

        for json_file in sorted(path.rglob("*.json")):
            try:
                json.loads(json_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON: {json_file.relative_to(path)}: {exc}")

        project_path = path / "project.json"
        profile = "freeform"
        if project_path.exists():
            try:
                project = json.loads(project_path.read_text(encoding="utf-8"))
                profile = project.get("profile") or "freeform"
            except json.JSONDecodeError:
                profile = "freeform"
        else:
            errors.append("missing required artifact: project.json")

        required_artifacts = PROFILES.get(profile, PROFILES["freeform"])["required_artifacts"]
        for artifact in required_artifacts:
            if not (path / artifact).exists():
                errors.append(f"missing required artifact: {artifact}")

        gaps_path = path / "hardening" / "initial-gaps.json"
        if gaps_path.exists():
            try:
                gaps = json.loads(gaps_path.read_text(encoding="utf-8"))
                if not gaps.get("gaps"):
                    warnings.append("hardening/initial-gaps.json has no gaps")
            except json.JSONDecodeError:
                pass

        return {
            "valid": not errors,
            "profile": profile,
            "errors": errors,
            "warnings": warnings,
        }


def collect_files(source_path: Path) -> tuple[list[Path], list[dict[str, str]]]:
    ignored: list[dict[str, str]] = []
    if source_path.is_file():
        return [source_path], ignored

    files: list[Path] = []
    for path in sorted(source_path.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(source_path)
        if any(part in IGNORED_DIRS for part in relative.parts):
            ignored.append({"path": portable(relative), "reason": "ignored directory"})
            continue
        if not is_supported(path):
            ignored.append({"path": portable(relative), "reason": "unsupported extension"})
            continue
        try:
            size = path.stat().st_size
        except OSError:
            ignored.append({"path": portable(relative), "reason": "stat failed"})
            continue
        if size > MAX_TEXT_BYTES and path.suffix.lower() not in {".pdf", ".docx", ".xlsx", ".pptx"}:
            ignored.append({"path": portable(relative), "reason": "file too large"})
            continue
        files.append(path)
    return files, ignored


def is_supported(path: Path) -> bool:
    suffix = path.suffix.lower()
    return (
        suffix in LANGUAGE_BY_SUFFIX
        or suffix in DOCUMENT_SUFFIXES
        or suffix in DATA_SUFFIXES
        or path.name in CONFIG_NAMES
    )


def load_source_file(root: Path, path: Path) -> SourceFile:
    relative = path.relative_to(root) if root.is_dir() else Path(path.name)
    suffix = path.suffix.lower()
    language = LANGUAGE_BY_SUFFIX.get(suffix)
    kind = detect_content_kind(path, language)
    size = path.stat().st_size
    text = read_text(path, kind)
    return SourceFile(path, relative, suffix, size, kind, language, mask_secrets(text))


def detect_content_kind(path: Path, language: str | None) -> str:
    suffix = path.suffix.lower()
    if language:
        if language in {"html", "css", "scss", "sass", "less", "dart", "typescript", "javascript"}:
            return "code"
        return "code"
    if suffix in DOCUMENT_SUFFIXES:
        return "documentation"
    if suffix in {".xlsx", ".csv"}:
        return "data"
    if suffix in DATA_SUFFIXES or path.name in CONFIG_NAMES:
        return "configuration"
    return "unknown"


def read_text(path: Path, kind: str) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf(path)
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".xlsx":
        return read_xlsx(path)
    if suffix == ".pptx":
        return read_pptx(path)
    if suffix == ".csv":
        return read_csv(path)
    try:
        raw = path.read_bytes()
    except OSError:
        return ""
    if b"\x00" in raw[:4096]:
        return ""
    return raw.decode("utf-8-sig", errors="replace")


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        return ""
    try:
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def read_docx(path: Path) -> str:
    return read_office_xml(path, "word/document.xml")


def read_pptx(path: Path) -> str:
    chunks: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            for name in sorted(archive.namelist()):
                if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                    chunks.append(xml_text(archive.read(name)))
    except (OSError, zipfile.BadZipFile):
        return ""
    return "\n".join(chunks)


def read_xlsx(path: Path) -> str:
    chunks: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            shared = []
            if "xl/sharedStrings.xml" in archive.namelist():
                shared = xml_text(archive.read("xl/sharedStrings.xml")).splitlines()
            for name in sorted(archive.namelist()):
                if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                    text = xml_text(archive.read(name))
                    chunks.append(text)
            if shared:
                chunks.append("\n".join(shared))
    except (OSError, zipfile.BadZipFile):
        return ""
    return "\n".join(chunks)


def read_office_xml(path: Path, member: str) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            return xml_text(archive.read(member))
    except (OSError, KeyError, zipfile.BadZipFile):
        return ""


def xml_text(raw: bytes) -> str:
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError:
        return raw.decode("utf-8", errors="replace")
    return "\n".join(node.text.strip() for node in root.iter() if node.text and node.text.strip())


def read_csv(path: Path) -> str:
    try:
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            rows = list(csv.reader(handle))
    except OSError:
        return ""
    return "\n".join(", ".join(row) for row in rows[:50])


def resolve_profile(source_files: list[SourceFile], requested: str = "auto") -> str:
    if requested != "auto":
        if requested not in PROFILES:
            raise KnowledgeGeneratorError(f"unknown profile: {requested}")
        return requested

    languages = {item.language for item in source_files if item.language}
    kinds = {item.content_kind for item in source_files}
    has_code = "code" in kinds
    has_docs = "documentation" in kinds
    has_data = "data" in kinds or "configuration" in kinds
    frontend_languages = {"dart", "html", "css", "scss", "sass", "less", "typescript", "javascript"}
    backend_languages = languages - frontend_languages

    if has_code and not backend_languages and languages & frontend_languages:
        return "frontend-app"
    if has_code:
        return "code-project"
    if has_docs and has_data:
        return "mixed-knowledge"
    if has_docs:
        return "documentation-set"
    if has_data:
        return "data-domain"
    return "freeform"


def detect_signals(source_files: list[SourceFile]) -> dict[str, bool]:
    combined = "\n".join(item.text[:20_000] for item in source_files).lower()
    paths = " ".join(portable(item.relative_path).lower() for item in source_files)
    return {
        "api": any(token in combined or token in paths for token in ["http", "route", "controller", "endpoint", "fetch(", "axios"]),
        "database": any(token in combined or token in paths for token in ["select ", "insert ", "migration", "schema", "table", "db"]),
        "frontend": any(language in {item.language for item in source_files} for language in ["dart", "html", "css", "scss", "typescript"]),
        "support": any(token in combined for token in ["runbook", "troubleshooting", "symptom", "incident", "playbook"]),
        "business": any(token in combined for token in ["regra", "processo", "jornada", "ator", "policy", "decision"]),
        "integration": any(token in combined for token in ["soap", "rest", "sftp", "webhook", "client", "token"]),
    }


def build_documents(
    *,
    source_path: Path,
    source_files: list[SourceFile],
    inspect: dict[str, Any],
    profile: str,
    project_id: str,
) -> dict[str, str]:
    source_index = {
        "knowledge_version": knowledge_version(),
        "project_id": project_id,
        "source_path": str(source_path),
        "files": [
            item.as_index_item(f"source-{index}")
            for index, item in enumerate(source_files, start=1)
        ],
        "ignored": inspect["source"]["ignored"],
    }
    project = {
        "knowledge_version": knowledge_version(),
        "profile": profile,
        "project": {
            "id": project_id,
            "name": project_id,
            "source_path": str(source_path),
            "description": "Knowledge gerado automaticamente a partir da fonte informada.",
        },
        "inventory_policy": {
            "format": "profile-driven-static-knowledge",
            "source_of_truth": "arquivos observados na fonte local",
            "do_not_store": [
                "senhas",
                "tokens",
                "api keys",
                "cookies",
                "certificados",
                "private keys",
                "connection strings",
                "payloads pessoais completos",
            ],
        },
    }

    gaps = build_gaps(source_files, profile, inspect)
    documents: dict[str, str] = {
        "README.md": render_readme(project_id, profile),
        "project.json": dump_json(project),
        "source-index.json": dump_json(source_index),
        "coverage-assessment.md": render_coverage(project_id, profile, source_files, inspect, gaps),
        "hardening/initial-gaps.json": dump_json(
            {
                "knowledge_version": knowledge_version(),
                "project_id": project_id,
                "profile": profile,
                "gaps": gaps,
            }
        ),
    }

    if profile in {"code-project", "frontend-app", "mixed-knowledge"} and any(
        item.content_kind == "code" for item in source_files
    ):
        code_inventory = build_code_inventory(project_id, source_files)
        documents["code-inventory.json"] = dump_json(code_inventory)
    if profile == "frontend-app":
        documents["frontend-inventory.json"] = dump_json(build_frontend_inventory(project_id, source_files))
    if profile in {"documentation-set", "mixed-knowledge"} and any(
        item.content_kind == "documentation" for item in source_files
    ):
        documents["document-map.json"] = dump_json(build_document_map(project_id, source_files))
    if profile == "data-domain":
        documents["data-inventory.json"] = dump_json(build_data_inventory(project_id, source_files))
    if profile == "business-domain":
        documents["domain.json"] = dump_json(build_generic_profile_artifact(project_id, profile, source_files))
    if profile == "integration-docs":
        documents["integration.json"] = dump_json(build_generic_profile_artifact(project_id, profile, source_files))
    if profile == "support-operations":
        documents["operations.json"] = dump_json(build_generic_profile_artifact(project_id, profile, source_files))

    return documents


def build_code_inventory(project_id: str, source_files: list[SourceFile]) -> dict[str, Any]:
    code_files = [item for item in source_files if item.content_kind == "code"]
    languages = sorted({item.language for item in code_files if item.language})
    symbols: list[dict[str, Any]] = []
    env_keys: set[str] = set()
    logs: list[dict[str, str]] = []
    integrations: list[dict[str, str]] = []

    for item in code_files:
        symbols.extend(extract_symbols(item))
        env_keys.update(extract_env_keys(item.text))
        logs.extend(extract_log_signals(item))
        integrations.extend(extract_integration_signals(item))

    return {
        "knowledge_version": knowledge_version(),
        "project_id": project_id,
        "artifact": "code-inventory",
        "languages": languages,
        "files": [
            {
                "path": portable(item.relative_path),
                "language": item.language,
                "size_bytes": item.size,
            }
            for item in code_files
        ],
        "symbols": symbols,
        "environment_keys": sorted(env_keys),
        "log_signals": logs,
        "integration_signals": integrations,
    }


def extract_symbols(item: SourceFile) -> list[dict[str, Any]]:
    text = item.text
    path = portable(item.relative_path)
    patterns: list[tuple[str, str]]
    if item.language == "python":
        patterns = [(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", "class"), (r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)", "function")]
    elif item.language in {"typescript", "javascript", "dart"}:
        patterns = [
            (r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)", "class"),
            (r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)", "function"),
            (r"\b(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\(", "function"),
        ]
    elif item.language == "csharp":
        patterns = [
            (r"\b(?:class|record)\s+([A-Za-z_][A-Za-z0-9_]*)", "class"),
            (r"\binterface\s+([A-Za-z_][A-Za-z0-9_]*)", "interface"),
            (r"\b(?:public|private|protected|internal)\s+(?:static\s+)?[\w<>]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", "method"),
        ]
    else:
        patterns = [(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)", "class"), (r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)", "function")]

    symbols: list[dict[str, Any]] = []
    for pattern, kind in patterns:
        for match in re.finditer(pattern, text, flags=re.MULTILINE):
            symbols.append(
                {
                    "name": match.group(1),
                    "kind": kind,
                    "language": item.language,
                    "source": path,
                }
            )
    if item.language == "html":
        for match in re.finditer(r"<form\b[^>]*?(?:action=[\"']([^\"']+)[\"'])?", text, flags=re.I):
            symbols.append({"name": f"form:{match.group(1) or 'unknown'}", "kind": "form", "language": "html", "source": path})
    if item.language in {"css", "scss", "sass", "less"}:
        for match in re.finditer(r"--([A-Za-z0-9_-]+)\s*:", text):
            symbols.append({"name": f"--{match.group(1)}", "kind": "design-token", "language": item.language, "source": path})
    return symbols


def extract_env_keys(text: str) -> set[str]:
    keys: set[str] = set()
    patterns = [
        r"os\.environ\.get\([\"']([A-Z0-9_]+)[\"']",
        r"process\.env\.([A-Z0-9_]+)",
        r"Environment\.GetEnvironmentVariable\([\"']([A-Z0-9_]+)[\"']",
    ]
    for pattern in patterns:
        keys.update(re.findall(pattern, text))
    return keys


def extract_log_signals(item: SourceFile) -> list[dict[str, str]]:
    signals = []
    for token in ["logger", "console.log", "print(", "correlation_id", "trace_id", "request_id"]:
        if token.lower() in item.text.lower():
            signals.append({"source": portable(item.relative_path), "signal": token})
    return signals


def extract_integration_signals(item: SourceFile) -> list[dict[str, str]]:
    signals = []
    for token in ["fetch(", "axios", "HttpClient", "requests.", "urllib", "SOAP", "RestTemplate"]:
        if token.lower() in item.text.lower():
            signals.append({"source": portable(item.relative_path), "signal": token})
    return signals


def build_frontend_inventory(project_id: str, source_files: list[SourceFile]) -> dict[str, Any]:
    frontend_files = [
        item
        for item in source_files
        if item.language in {"dart", "html", "css", "scss", "sass", "less", "typescript", "javascript"}
    ]
    return {
        "knowledge_version": knowledge_version(),
        "project_id": project_id,
        "artifact": "frontend-inventory",
        "files": [
            {
                "path": portable(item.relative_path),
                "language": item.language,
                "signals": frontend_signals(item),
            }
            for item in frontend_files
        ],
    }


def frontend_signals(item: SourceFile) -> list[str]:
    signals = []
    lowered = item.text.lower()
    for token in ["widget", "statelesswidget", "statefulwidget", "<form", "@media", ":root", "router", "route"]:
        if token in lowered:
            signals.append(token)
    return signals


def build_document_map(project_id: str, source_files: list[SourceFile]) -> dict[str, Any]:
    docs = [item for item in source_files if item.content_kind == "documentation"]
    return {
        "knowledge_version": knowledge_version(),
        "project_id": project_id,
        "artifact": "document-map",
        "documents": [
            {
                "path": portable(item.relative_path),
                "size_bytes": item.size,
                "observed_headings": re.findall(r"^#{1,6}\s+(.+)$", item.text, flags=re.MULTILINE)[:20],
                "preview": compact(item.text)[:500],
            }
            for item in docs
        ],
    }


def build_data_inventory(project_id: str, source_files: list[SourceFile]) -> dict[str, Any]:
    data_files = [item for item in source_files if item.content_kind in {"data", "configuration"}]
    return {
        "knowledge_version": knowledge_version(),
        "project_id": project_id,
        "artifact": "data-inventory",
        "files": [
            {
                "path": portable(item.relative_path),
                "format": item.suffix.lstrip(".") or item.path.name,
                "preview": compact(item.text)[:500],
            }
            for item in data_files
        ],
    }


def build_generic_profile_artifact(project_id: str, profile: str, source_files: list[SourceFile]) -> dict[str, Any]:
    """Build a structured artifact for domain-oriented profiles.

    Emits structured items with {id, type, summary, evidence, source, status}
    instead of a plain list of frequent terms.  The heuristic extracts candidate
    rules/actors/processes/decisions from the source text so that a coupled LLM
    can review and enrich them rather than starting from a term frequency list.
    """
    items = _extract_structured_items(profile, source_files)
    return {
        "knowledge_version": knowledge_version(),
        "project_id": project_id,
        "profile": profile,
        "items": items,
        "open_questions": [
            "Revisar itens extraidos automaticamente e confirmar quais representam "
            "regras, decisoes, contratos ou processos reais com base na fonte.",
            "Para cada item com status 'inference', validar a evidencia citada "
            "antes de usar em operacao critica.",
        ],
    }


# ---------------------------------------------------------------------------
# Structured extraction helpers
# ---------------------------------------------------------------------------

_RULE_KEYWORDS = re.compile(
    r"(?i)\b(regra|rule|policy|politica|obrigatorio|mandatory|deve|should|must|proibido|forbidden|nao deve|nao pode)\b"
)
_ACTOR_KEYWORDS = re.compile(r"(?i)\b(ator|actor|usuario|user|cliente|client|operador|operator|sistema|system|servico|service)\b")
_PROCESS_KEYWORDS = re.compile(r"(?i)\b(processo|process|fluxo|flow|jornada|journey|etapa|step|fase|stage|workflow)\b")
_DECISION_KEYWORDS = re.compile(r"(?i)\b(decisao|decision|escolha|choice|if|when|quando|condicao|condition)\b")
_INTEGRATION_KEYWORDS = re.compile(r"(?i)\b(endpoint|route|url|api|soap|rest|sftp|webhook|payload|request|response|auth|token|certificate)\b")
_OPERATION_KEYWORDS = re.compile(r"(?i)\b(runbook|playbook|troubleshooting|troubleshoot|sintoma|symptom|incident|incidente|escalar|escalate|resolver|resolve)\b")


def _sentence_windows(text: str, window: int = 200) -> list[str]:
    """Split text into overlapping windows around newlines for evidence extraction."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    windows = []
    for i, line in enumerate(lines):
        chunk = " ".join(lines[max(0, i - 1): i + 2])
        if chunk:
            windows.append(chunk[:window])
    return windows


def _extract_structured_items(profile: str, source_files: list[SourceFile]) -> list[dict[str, Any]]:
    """Extract structured items from source files according to the profile type."""
    if profile == "business-domain":
        keyword_map = [
            ("rule", _RULE_KEYWORDS),
            ("actor", _ACTOR_KEYWORDS),
            ("process", _PROCESS_KEYWORDS),
            ("decision", _DECISION_KEYWORDS),
        ]
    elif profile == "integration-docs":
        keyword_map = [
            ("contract", _INTEGRATION_KEYWORDS),
        ]
    elif profile == "support-operations":
        keyword_map = [
            ("playbook", _OPERATION_KEYWORDS),
        ]
    else:
        keyword_map = [
            ("rule", _RULE_KEYWORDS),
            ("process", _PROCESS_KEYWORDS),
        ]

    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    item_index = 1

    for item_type, pattern in keyword_map:
        for source_file in source_files:
            source_path = portable(source_file.relative_path)
            for window in _sentence_windows(source_file.text):
                if pattern.search(window):
                    key = window[:80].lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append(
                        {
                            "id": f"{item_type}-{item_index}",
                            "type": item_type,
                            "summary": window[:200],
                            "evidence": window[:200],
                            "source": source_path,
                            "status": "inference",
                        }
                    )
                    item_index += 1
                    if len(items) >= 50:
                        return items

    # Fallback: if no structured items were found, emit a single placeholder gap entry
    if not items:
        items.append(
            {
                "id": f"{profile}-no-structured-items",
                "type": "gap",
                "summary": "Nenhum item estruturado extraido automaticamente; revisao manual necessaria.",
                "evidence": "",
                "source": "",
                "status": "gap",
            }
        )

    return items


def extract_terms(source_files: list[SourceFile]) -> list[str]:
    counts: dict[str, int] = {}
    stopwords = {"function", "return", "class", "public", "private", "import", "export", "const", "string", "true", "false"}
    for item in source_files:
        for raw in re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_-]{3,}", item.text):
            term = raw.strip("_-")
            lowered = term.lower()
            if lowered in stopwords:
                continue
            counts[term] = counts.get(term, 0) + 1
    return [term for term, _count in sorted(counts.items(), key=lambda entry: (-entry[1], entry[0]))]


def build_gaps(source_files: list[SourceFile], profile: str, inspect: dict[str, Any]) -> list[dict[str, str]]:
    gaps = [
        {
            "id": "manual-review-required",
            "severity": "medium",
            "description": "Knowledge gerado por heuristicas locais; revisar regras de negocio e decisoes antes de uso operacional critico.",
        }
    ]
    if inspect["source"]["ignored_count"]:
        gaps.append(
            {
                "id": "ignored-files-present",
                "severity": "low",
                "description": f"{inspect['source']['ignored_count']} arquivos foram ignorados por diretorio, extensao, tamanho ou erro de leitura.",
            }
        )
    if profile in {"code-project", "frontend-app"} and not any(item.content_kind == "code" for item in source_files):
        gaps.append(
            {
                "id": "profile-without-code",
                "severity": "high",
                "description": "Profile de codigo selecionado, mas nenhum arquivo de codigo suportado foi detectado.",
            }
        )
    if any(item.suffix == ".pdf" and not item.text for item in source_files):
        gaps.append(
            {
                "id": "pdf-text-unavailable",
                "severity": "medium",
                "description": "Um ou mais PDFs nao tiveram texto extraivel; OCR pode ser necessario.",
            }
        )
    return gaps


def render_readme(project_id: str, profile: str) -> str:
    return (
        f"# Knowledge: {project_id}\n\n"
        f"Profile: `{profile}`.\n\n"
        "Este diretorio foi gerado automaticamente pelo `knowledge-generator`.\n"
        "Revise lacunas em `hardening/initial-gaps.json` antes de usar como fonte operacional madura.\n"
    )


def render_coverage(
    project_id: str,
    profile: str,
    source_files: list[SourceFile],
    inspect: dict[str, Any],
    gaps: list[dict[str, str]],
) -> str:
    languages = ", ".join(inspect["source"]["languages"]) or "nenhuma"
    kinds = ", ".join(inspect["source"]["content_kinds"]) or "nenhum"
    return "\n".join(
        [
            "# Knowledge Coverage Assessment",
            "",
            f"Projeto: `{project_id}`",
            f"Profile: `{profile}`",
            f"Arquivos analisados: {len(source_files)}",
            f"Arquivos ignorados: {inspect['source']['ignored_count']}",
            f"Linguagens detectadas: {languages}",
            f"Tipos de conteudo: {kinds}",
            "",
            "## Lacunas",
            "",
            *[f"- {gap['id']}: {gap['description']}" for gap in gaps],
            "",
        ]
    )


def resolve_output_dir(output_dir: str | None, source_path: Path) -> Path:
    if output_dir:
        return Path(output_dir).expanduser().resolve()
    if source_path.is_dir():
        return source_path / "knowledge"
    return source_path.parent / "knowledge"


def ensure_output_dir(path: Path, yes_create_dir: bool) -> None:
    if path.exists() and not path.is_dir():
        raise KnowledgeGeneratorError(f"output path exists and is not a directory: {path}")
    if not path.exists():
        if not yes_create_dir:
            raise KnowledgeGeneratorError(f"output directory does not exist; pass --yes-create-dir: {path}")
        path.mkdir(parents=True, exist_ok=True)


def write_documents(output_dir: Path, documents: dict[str, str], yes_overwrite: bool) -> None:
    for relative, content in documents.items():
        target = output_dir / relative
        if target.exists() and not yes_overwrite:
            raise KnowledgeGeneratorError(f"artifact already exists; pass --yes-overwrite: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def mask_secrets(value: str) -> str:
    text = value
    for pattern, replacement in SECRET_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def compact(value: str) -> str:
    text = html.unescape(value)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def portable(path: Path) -> str:
    return path.as_posix()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "knowledge-source"


def knowledge_version() -> str:
    return f"{date.today().isoformat()}.auto"
