"""Template and planning operation runners for excel-workbook-builder."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil

from workbook_support import (
    append_changelog,
    generate_workbook_from_dataset,
    parse_template_manifest,
    resolve_templates_root,
    slugify,
    template_dir,
    version_dir,
    write_input_schema_md,
    write_input_schema_xlsx,
    write_manifest_data,
    write_sheet_map,
    write_template_manifest,
    write_usage_notes,
)


def run(operation: str) -> int:
    try:
        if operation == "plan-workbook":
            return plan_workbook()
        if operation == "create-template":
            return create_template()
        if operation == "create-template-version":
            return create_template_version()
        if operation == "refine-template":
            return create_template_version(refine=True)
        if operation == "promote-template-version":
            return set_template_version_status(promote=True)
        if operation == "deprecate-template-version":
            return set_template_version_status(deprecate=True)
        if operation == "compare-template-versions":
            return compare_template_versions()
        raise ValueError(f"unsupported operation: {operation}")
    except Exception as exc:
        print(f"error: {exc}")
        return 1


def plan_workbook() -> int:
    parser = argparse.ArgumentParser(description="Plan a workbook")
    parser.add_argument("--brief", required=True)
    parser.add_argument("--template-id")
    parser.add_argument("--data-schema")
    parser.add_argument("--output")
    args = parser.parse_args()
    markdown = "\n".join(
        [
            "# Workbook Plan",
            "",
            f"- Template: {args.template_id or '-'}",
            f"- Data schema: {args.data_schema or '-'}",
            "",
            "## Brief",
            "",
            args.brief,
            "",
            "## Proposed Sheets",
            "",
            "- Inputs",
            "- Data",
            "- Summary",
            "- Quality",
            "",
            "## Quality Gates",
            "",
            "- Validate source data.",
            "- Scan formula errors.",
            "- Render preview.",
        ]
    ) + "\n"
    write_or_print(markdown, args.output)
    return 0


def create_template() -> int:
    parser = argparse.ArgumentParser(description="Create a starter Excel template")
    parser.add_argument("--brief", required=True)
    parser.add_argument("--template-id", default="workbook-template")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    dataset = {
        "source": "template brief",
        "columns": ["field", "description", "required"],
        "rows": [
            {"field": "dataset_name", "description": "Nome da base", "required": "yes"},
            {"field": "source_file", "description": "Arquivo de origem", "required": "yes"},
            {"field": "business_notes", "description": args.brief, "required": "no"},
        ],
    }
    generate_workbook_from_dataset(dataset, Path(args.output).expanduser().resolve(), title=args.template_id)
    print(f"Template criado: {Path(args.output).expanduser().resolve()}")
    return 0


def create_template_version(refine: bool = False) -> int:
    parser = argparse.ArgumentParser(description="Create Excel template version")
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--template")
    parser.add_argument("--base-version")
    parser.add_argument("--version", required=True)
    parser.add_argument("--templates-root")
    parser.add_argument("--name")
    parser.add_argument("--status", default="draft")
    parser.add_argument("--feedback")
    args = parser.parse_args()
    root = resolve_templates_root(args.templates_root)
    template_id = slugify(args.template_id)
    target_dir = version_dir(root, template_id, args.version)
    if target_dir.exists():
        raise ValueError(f"template version already exists: {template_id} {args.version}")
    target_dir.mkdir(parents=True, exist_ok=False)
    source = resolve_source_template(root, template_id, args.template, args.base_version)
    shutil.copyfile(source, target_dir / "template.xlsx")
    manifest_path = template_dir(root, template_id) / "template.yaml"
    if not manifest_path.exists():
        write_template_manifest(root, template_id, args.name or template_id, args.version, args.status)
    else:
        append_manifest_version(manifest_path, args.version, args.status)
    write_sheet_map(root, template_id, args.version)
    write_input_schema_xlsx(root, template_id, args.version)
    write_input_schema_md(root, template_id, args.version)
    write_usage_notes(root, template_id, args.version)
    message = "Template refinado." if refine else "Versao de template criada."
    if args.feedback:
        message += f" Feedback: {args.feedback}"
    append_changelog(root, template_id, args.version, message)
    print(f"Template version criado: {template_id} {args.version}")
    return 0


def resolve_source_template(root: Path, template_id: str, template: str | None, base_version: str | None) -> Path:
    if template:
        source = Path(template).expanduser().resolve()
    elif base_version:
        source = version_dir(root, template_id, base_version) / "template.xlsx"
    else:
        raise ValueError("--template or --base-version is required")
    if not source.exists():
        raise ValueError(f"template source not found: {source}")
    return source


def set_template_version_status(promote: bool = False, deprecate: bool = False) -> int:
    parser = argparse.ArgumentParser(description="Set template version status")
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--template-version", required=True)
    parser.add_argument("--templates-root")
    args = parser.parse_args()
    root = resolve_templates_root(args.templates_root)
    template_id = slugify(args.template_id)
    manifest_path = template_dir(root, template_id) / "template.yaml"
    if not manifest_path.exists():
        raise ValueError(f"template not found: {template_id}")
    status = "validated" if promote else "deprecated" if deprecate else "draft"
    update_manifest_status(manifest_path, args.template_version, status, current=promote)
    append_changelog(root, template_id, args.template_version, f"Status atualizado para `{status}`.")
    print(f"Template atualizado: {template_id} {args.template_version} {status}")
    return 0


def compare_template_versions() -> int:
    parser = argparse.ArgumentParser(description="Compare template versions")
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--left-version", required=True)
    parser.add_argument("--right-version", required=True)
    parser.add_argument("--templates-root")
    parser.add_argument("--output")
    args = parser.parse_args()
    root = resolve_templates_root(args.templates_root)
    template_id = slugify(args.template_id)
    left = version_dir(root, template_id, args.left_version)
    right = version_dir(root, template_id, args.right_version)
    if not left.exists() or not right.exists():
        raise ValueError("both template versions must exist")
    left_files = sorted(path.name for path in left.iterdir() if path.is_file())
    right_files = sorted(path.name for path in right.iterdir() if path.is_file())
    markdown = "\n".join(
        [
            "# Template Version Comparison",
            "",
            f"- Template: {template_id}",
            f"- Left: {args.left_version}",
            f"- Right: {args.right_version}",
            "",
            "## Added",
            "",
            *([f"- {item}" for item in sorted(set(right_files) - set(left_files))] or ["- None"]),
            "",
            "## Removed",
            "",
            *([f"- {item}" for item in sorted(set(left_files) - set(right_files))] or ["- None"]),
        ]
    ) + "\n"
    write_or_print(markdown, args.output)
    return 0


def append_manifest_version(path: Path, version: str, status: str) -> None:
    manifest = parse_template_manifest(path)
    versions = manifest.setdefault("versions", [])
    if any(item.get("version") == version for item in versions):
        raise ValueError(f"template version already exists in manifest: {version}")
    versions.append(
        {
            "version": version,
            "status": status,
            "path": f"versions/{version}/template.xlsx",
            "input_schema": f"versions/{version}/input-schema.xlsx",
            "created_at": date.today().isoformat(),
            "notes": "template versionado pelo agente",
        }
    )
    if status == "validated":
        manifest["current_version"] = version
    write_manifest_data(path, manifest)


def update_manifest_status(path: Path, version: str, status: str, current: bool) -> None:
    manifest = parse_template_manifest(path)
    found = False
    for item in manifest.get("versions", []):
        if item.get("version") == version:
            item["status"] = status
            found = True
            break
    if not found:
        raise ValueError(f"template version not found in manifest: {version}")
    if current:
        manifest["current_version"] = version
    elif manifest.get("current_version") == version and status in {"deprecated", "archived"}:
        manifest["current_version"] = ""
    write_manifest_data(path, manifest)


def write_or_print(markdown: str, output: str | None) -> None:
    if output:
        target = Path(output).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
