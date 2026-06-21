#!/usr/bin/env python3
"""Runner for presentation-deck-builder/register-template."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from template_support import (  # noqa: E402
    append_changelog,
    copy_template,
    ensure_write_allowed,
    resolve_templates_root,
    slugify,
    template_dir,
    version_dir,
    write_input_schema_md,
    write_input_schema_xlsx,
    write_slide_map,
    write_template_manifest,
    write_usage_notes,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Register a versioned presentation template")
    parser.add_argument("--template", required=True)
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--name")
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--status", choices=["draft", "validated", "deprecated", "archived"], default="draft")
    parser.add_argument("--templates-root")
    parser.add_argument("--yes-save", action="store_true")
    args = parser.parse_args()

    try:
        source = Path(args.template).expanduser().resolve()
        if not source.exists():
            raise ValueError(f"template not found: {source}")
        if source.suffix.lower() not in {".pptx", ".ppt", ".potx"}:
            raise ValueError("template must be .pptx, .ppt, or .potx")

        root = resolve_templates_root(args.templates_root)
        template_id = slugify(args.template_id)
        name = args.name or template_id.replace("-", " ").title()
        target_dir = version_dir(root, template_id, args.version)
        if target_dir.exists():
            raise ValueError(f"template version already exists: {template_id} {args.version}")

        ensure_write_allowed(template_dir(root, template_id), args.yes_save, "template versionado")
        target_dir.mkdir(parents=True, exist_ok=False)
        copy_template(source, target_dir / "template.pptx")
        write_template_manifest(root, template_id, name, args.version, args.status)
        write_slide_map(root, template_id, args.version)
        write_input_schema_xlsx(root, template_id, args.version)
        write_input_schema_md(root, template_id, args.version)
        write_usage_notes(root, template_id, args.version)
        append_changelog(root, template_id, args.version, f"Template registrado com status `{args.status}`.")

        print(f"Template registrado: {template_id} {args.version}")
        print(f"Manifest: {template_dir(root, template_id) / 'template.yaml'}")
        print(f"Version dir: {target_dir}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
