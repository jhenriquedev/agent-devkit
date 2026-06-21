#!/usr/bin/env python3
"""Runner for excel-workbook-builder/generate-template-input-file."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import (  # noqa: E402
    parse_template_manifest,
    resolve_templates_root,
    slugify,
    template_dir,
    version_dir,
    write_input_schema_md,
    write_input_schema_xlsx,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Excel template input schema")
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--template-version")
    parser.add_argument("--templates-root")
    args = parser.parse_args()

    try:
        root = resolve_templates_root(args.templates_root)
        template_id = slugify(args.template_id)
        manifest_path = template_dir(root, template_id) / "template.yaml"
        if not manifest_path.exists():
            raise ValueError(f"template not found: {template_id}")
        manifest = parse_template_manifest(manifest_path)
        version = args.template_version or str(manifest.get("current_version") or "")
        if not version:
            versions = manifest.get("versions", [])
            version = versions[-1]["version"] if versions else ""
        if not version:
            raise ValueError("template has no version")
        target_dir = version_dir(root, template_id, version)
        if not target_dir.exists():
            raise ValueError(f"template version not found: {template_id} {version}")
        write_input_schema_xlsx(root, template_id, version)
        write_input_schema_md(root, template_id, version)
        print(f"Input schema gerado: {target_dir / 'input-schema.xlsx'}")
        print(f"Input schema Markdown: {target_dir / 'input-schema.md'}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

