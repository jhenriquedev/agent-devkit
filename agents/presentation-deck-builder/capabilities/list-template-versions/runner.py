#!/usr/bin/env python3
"""Runner for presentation-deck-builder/list-template-versions."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from template_support import parse_template_manifest, resolve_templates_root, slugify, template_dir  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="List template versions")
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--templates-root")
    args = parser.parse_args()
    try:
        root = resolve_templates_root(args.templates_root)
        template_id = slugify(args.template_id)
        manifest_path = template_dir(root, template_id) / "template.yaml"
        if not manifest_path.exists():
            raise ValueError(f"template not found: {template_id}")
        manifest = parse_template_manifest(manifest_path)
        print(f"# Template Versions: {manifest.get('id', template_id)}")
        print("")
        print(f"- Name: {manifest.get('name', '-')}")
        print(f"- Current version: {manifest.get('current_version', '-') or '-'}")
        print("")
        for item in manifest.get("versions", []):
            print(f"- {item.get('version')}  {item.get('status', '-')}  {item.get('path', '-')}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
