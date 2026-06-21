#!/usr/bin/env python3
"""Runner for excel-workbook-builder/generate-workbook-from-template."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from workbook_support import (  # noqa: E402
    generate_workbook_from_dataset,
    normalize_dataset,
    parse_template_manifest,
    resolve_templates_root,
    slugify,
    template_dir,
    version_dir,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate workbook from registered template")
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--template-version")
    parser.add_argument("--templates-root")
    parser.add_argument("--output")
    parser.add_argument("--title")
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
        if not version_dir(root, template_id, version).exists():
            raise ValueError(f"template version not found: {template_id} {version}")

        input_path = Path(args.input).expanduser().resolve()
        data = json.loads(input_path.read_text(encoding="utf-8"))
        dataset = normalize_dataset(data, source=data.get("source") or str(input_path))
        output = (
            Path(args.output).expanduser().resolve()
            if args.output
            else Path.cwd() / "docs" / "generated" / "excel-workbook-builder" / f"{template_id}.xlsx"
        )
        title = args.title or str(manifest.get("name") or template_id)
        generate_workbook_from_dataset(
            dataset,
            output,
            title=title,
            summary={"template_id": template_id, "template_version": version},
        )
        print(f"Workbook gerado: {output}")
        print(f"Template: {template_id} {version}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

