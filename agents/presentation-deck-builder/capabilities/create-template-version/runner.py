#!/usr/bin/env python3
"""Runner for presentation-deck-builder/create-template-version."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from template_support import (  # noqa: E402
    add_version_to_manifest,
    append_changelog,
    copy_version,
    parse_template_manifest,
    resolve_templates_root,
    slugify,
    template_dir,
    version_dir,
    write_input_schema_md,
    write_input_schema_xlsx,
    write_slide_map,
    write_usage_notes,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a new template version from base or file"
    )
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--new-version", required=True)
    parser.add_argument("--base-version")
    parser.add_argument("--template", help="path to updated .pptx/.ppt/.potx file")
    parser.add_argument("--templates-root")
    args = parser.parse_args()

    try:
        root = resolve_templates_root(args.templates_root)
        template_id = slugify(args.template_id)
        new_version = args.new_version
        manifest_path = template_dir(root, template_id) / "template.yaml"

        if not manifest_path.exists():
            print(f"template not found: {template_id}", file=sys.stderr)
            return 1

        manifest = parse_template_manifest(manifest_path)
        existing_versions = [str(v.get("version")) for v in manifest.get("versions", [])]

        if new_version in existing_versions:
            raise ValueError(
                f"version already exists: {template_id} {new_version}"
            )

        base_version = args.base_version or str(manifest.get("current_version") or "")
        if not base_version and existing_versions:
            base_version = existing_versions[-1]
        if not base_version:
            raise ValueError("no base_version available and no existing versions")

        base_dir = version_dir(root, template_id, base_version)
        if not base_dir.exists():
            raise ValueError(f"base version dir not found: {template_id} {base_version}")

        source_file: Path | None = None
        if args.template:
            source_file = Path(args.template).expanduser().resolve()
            if not source_file.exists():
                raise ValueError(f"template file not found: {source_file}")
            if source_file.suffix.lower() not in {".pptx", ".ppt", ".potx"}:
                raise ValueError("template must be .pptx, .ppt, or .potx")

        copy_version(root, template_id, base_version, new_version, source_file)
        write_slide_map(root, template_id, new_version)
        write_input_schema_xlsx(root, template_id, new_version)
        write_input_schema_md(root, template_id, new_version)
        write_usage_notes(root, template_id, new_version)
        add_version_to_manifest(root, template_id, new_version, "draft")
        append_changelog(
            root,
            template_id,
            new_version,
            f"Nova versao {new_version} criada a partir de {base_version}.",
        )

        new_dir = version_dir(root, template_id, new_version)
        print(f"Versao criada: {template_id} {new_version}")
        print(f"Version dir: {new_dir}")
        print(f"Status: draft")
        print(f"Manifest: {manifest_path}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
