#!/usr/bin/env python3
"""Runner for presentation-deck-builder/promote-template-version."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from template_support import (  # noqa: E402
    append_changelog,
    parse_template_manifest,
    resolve_templates_root,
    set_current_version,
    set_version_status,
    slugify,
    template_dir,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote a template version to current_version"
    )
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--template-version", required=True)
    parser.add_argument("--templates-root")
    parser.add_argument(
        "--yes-confirm",
        action="store_true",
        help="skip interactive confirmation",
    )
    args = parser.parse_args()

    try:
        root = resolve_templates_root(args.templates_root)
        template_id = slugify(args.template_id)
        version = args.template_version
        manifest_path = template_dir(root, template_id) / "template.yaml"

        if not manifest_path.exists():
            print(f"template not found: {template_id}", file=sys.stderr)
            return 1

        manifest = parse_template_manifest(manifest_path)
        versions = manifest.get("versions", [])
        version_entry = next(
            (v for v in versions if str(v.get("version")) == version), None
        )
        if version_entry is None:
            print(
                f"template version not found in manifest: {template_id} {version}",
                flush=True,
            )
            return 1

        if not args.yes_confirm:
            answer = input(
                f"Promover versao {version} de '{template_id}' para current_version? [s/N] "
            ).strip().lower()
            if answer not in {"s", "sim", "y", "yes"}:
                print("promocao cancelada pelo usuario", file=sys.stderr)
                return 1

        previous_current = str(manifest.get("current_version") or "")
        set_current_version(root, template_id, version)
        set_version_status(root, template_id, version, "validated")
        append_changelog(
            root,
            template_id,
            version,
            f"Versao {version} promovida para current_version (anterior: {previous_current or 'nenhuma'}).",
        )

        print(f"Versao promovida: {template_id} {version}")
        print(f"current_version anterior: {previous_current or '(nenhuma)'}")
        print(f"current_version atual:    {version}")
        print(f"Manifest: {manifest_path}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
