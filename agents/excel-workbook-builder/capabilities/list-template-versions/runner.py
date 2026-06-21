#!/usr/bin/env python3
"""Runner for excel-workbook-builder/list-template-versions."""

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
)


def main() -> int:
    parser = argparse.ArgumentParser(description="List Excel template versions")
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--templates-root")
    args = parser.parse_args()

    try:
        root = resolve_templates_root(args.templates_root)
        template_id = slugify(args.template_id)
        manifest_path = template_dir(root, template_id) / "template.yaml"
        if not manifest_path.exists():
            raise ValueError(f"template not found: {template_id}")
        data = parse_template_manifest(manifest_path)
        lines = [
            f"# Excel Template Versions: {template_id}",
            "",
            f"- Name: {data.get('name') or '-'}",
            f"- Current version: {data.get('current_version') or '-'}",
            "",
        ]
        for item in data.get("versions", []):
            lines.append(
                f"- {item.get('version') or '-'}  "
                f"{item.get('status') or '-'}  "
                f"{item.get('path') or '-'}"
            )
        print("\n".join(lines).rstrip() + "\n")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

