#!/usr/bin/env python3
"""Runner for presentation-deck-builder/refine-template.

Creates a new version from a base version applying a change_request.
The base validated version is NEVER modified.
"""

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


def _bump_version(version: str, bump: str) -> str:
    """Compute next semver given bump type: patch | minor | major."""
    parts = version.split(".")
    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except (IndexError, ValueError):
        return version + "-refined"
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refine a template by creating a new version"
    )
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--change-request", required=True)
    parser.add_argument("--base-version")
    parser.add_argument("--new-version")
    parser.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        default="patch",
        help="semver bump type (default: patch)",
    )
    parser.add_argument("--templates-root")
    args = parser.parse_args()

    try:
        root = resolve_templates_root(args.templates_root)
        template_id = slugify(args.template_id)
        manifest_path = template_dir(root, template_id) / "template.yaml"

        if not manifest_path.exists():
            print(f"template not found: {template_id}", file=sys.stderr)
            return 1

        manifest = parse_template_manifest(manifest_path)
        base_version = args.base_version or str(manifest.get("current_version") or "")
        if not base_version:
            existing = manifest.get("versions", [])
            base_version = str(existing[-1].get("version")) if existing else ""
        if not base_version:
            raise ValueError("no base_version available")

        base_dir = version_dir(root, template_id, base_version)
        if not base_dir.exists():
            raise ValueError(f"base version dir not found: {template_id} {base_version}")

        # Verify base is not being overwritten
        base_entries = manifest.get("versions", [])
        base_entry = next(
            (v for v in base_entries if str(v.get("version")) == base_version), None
        )
        if base_entry and str(base_entry.get("status")) == "validated":
            # Enforced: must create new version — never overwrite validated
            pass  # new version creation below is the enforcement

        existing_versions = {str(v.get("version")) for v in manifest.get("versions", [])}
        new_version = args.new_version
        if not new_version:
            new_version = _bump_version(base_version, args.bump)
            # Ensure uniqueness
            candidate = new_version
            counter = 1
            while candidate in existing_versions:
                candidate = new_version + f"-r{counter}"
                counter += 1
            new_version = candidate

        if new_version in existing_versions:
            raise ValueError(f"version already exists: {template_id} {new_version}")

        copy_version(root, template_id, base_version, new_version)
        write_slide_map(root, template_id, new_version)
        write_input_schema_xlsx(root, template_id, new_version)
        write_input_schema_md(root, template_id, new_version)
        write_usage_notes(root, template_id, new_version)
        add_version_to_manifest(root, template_id, new_version, "draft")
        append_changelog(
            root,
            template_id,
            new_version,
            f"Refinamento de {base_version}: {args.change_request}. Bump: {args.bump}.",
        )

        new_dir = version_dir(root, template_id, new_version)
        print(f"Versao refinada: {template_id} {new_version}")
        print(f"Base: {base_version}")
        print(f"Bump: {args.bump}")
        print(f"Version dir: {new_dir}")
        print(f"Status: draft")
        print(f"Manifest: {manifest_path}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
