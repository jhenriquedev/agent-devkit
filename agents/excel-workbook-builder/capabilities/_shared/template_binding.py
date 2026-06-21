"""Template binding helpers for excel-workbook-builder capabilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workbook_support import parse_template_manifest, slugify, template_dir, version_dir


def resolve_template_version(
    root: Path,
    template_id: str,
    requested_version: str | None,
) -> tuple[str, Path]:
    normalized_id = slugify(template_id)
    manifest_path = template_dir(root, normalized_id) / "template.yaml"
    if not manifest_path.exists():
        raise ValueError(f"template not found: {normalized_id}")
    manifest = parse_template_manifest(manifest_path)
    version = requested_version or str(manifest.get("current_version") or "")
    if not version:
        versions = manifest.get("versions", [])
        version = versions[-1]["version"] if versions else ""
    if not version:
        raise ValueError(f"template has no version: {normalized_id}")
    directory = version_dir(root, normalized_id, version)
    template_path = directory / "template.xlsx"
    if not template_path.exists():
        raise ValueError(f"template file not found: {template_path}")
    return version, template_path


def default_data_binding(dataset: dict[str, Any], sheet_name: str = "Data") -> dict[str, Any]:
    return {
        "mode": "replace_sheet",
        "sheet": sheet_name,
        "columns": dataset.get("columns", []),
        "rows": dataset.get("rows", []),
    }
