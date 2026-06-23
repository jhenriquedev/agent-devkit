#!/usr/bin/env python3
"""Runner for presentation-deck-builder/deprecate-template-version."""

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
    set_version_status,
    slugify,
    template_dir,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deprecate a template version without deleting files"
    )
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--template-version", required=True)
    parser.add_argument("--reason", default="")
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

        current = str(manifest.get("current_version") or "")
        is_current = current == version

        if is_current:
            print(
                f"AVISO: versao {version} e a current_version de '{template_id}'. "
                "Deprecar ira deixar o template sem current_version valida.",
                flush=True,
            )

        if not args.yes_confirm:
            answer = input(
                f"Deprecar versao {version} de '{template_id}'? [s/N] "
            ).strip().lower()
            if answer not in {"s", "sim", "y", "yes"}:
                print("deprecacao cancelada pelo usuario", file=sys.stderr)
                return 1

        set_version_status(root, template_id, version, "deprecated")
        reason_text = args.reason or "sem motivo informado"
        append_changelog(
            root,
            template_id,
            version,
            f"Versao {version} depreciada. Motivo: {reason_text}.",
        )

        print(f"Versao depreciada: {template_id} {version}")
        if is_current:
            print(
                f"AVISO: esta versao era a current_version. "
                "Defina uma nova current_version com promote-template-version."
            )
        print(f"Motivo: {reason_text}")
        print(f"Manifest: {manifest_path}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
