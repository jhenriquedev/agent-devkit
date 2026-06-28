"""Install AI DevKit host artifacts globally or into a project."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from cli.aikit import __version__
from cli.aikit.lock import GLOBAL_RUNTIME_DIR, PROJECT_RUNTIME_DIR, lock_path, write_lock


HOST_ALIASES = {
    "all": ("codex", "claude-code", "claude-desktop"),
    "codex": ("codex",),
    "claude-code": ("claude-code",),
    "claude-desktop": ("claude-desktop",),
    "claude-ai": ("claude-desktop",),
}


class InstallError(ValueError):
    """Raised when install arguments or source artifacts are invalid."""


def install_runtime(
    root: Path,
    *,
    scope: str,
    host: str = "all",
    target: Path | None = None,
    home: Path | None = None,
    dry_run: bool = False,
    profiles: list[str] | None = None,
) -> dict[str, Any]:
    """Install local AI DevKit host artifacts.

    The installer never requests or persists provider credentials. It writes
    only runtime discovery files and small host adapters.
    """

    if scope not in {"project", "global"}:
        raise InstallError(f"unsupported install scope: {scope}")
    hosts = resolve_hosts(host)
    root = root.resolve()
    base = resolve_base(scope, target=target, home=home)
    runtime_dir = base / (GLOBAL_RUNTIME_DIR if scope == "global" else PROJECT_RUNTIME_DIR)
    bin_dir = runtime_dir / "bin"
    config_path = runtime_dir / "config.yaml"
    runtime_lock_path = lock_path(base, scope)
    operations = build_operations(root, base, hosts)
    command_shims = build_command_shims(root, bin_dir)
    planned = [
        str(config_path),
        str(runtime_lock_path),
        *[str(path) for path in command_shims.values()],
        *[str(operation["destination"]) for operation in operations],
    ]
    written: list[str] = []

    if not dry_run:
        validate_sources(operations)
        validate_command_sources(root, command_shims)
        runtime_dir.mkdir(parents=True, exist_ok=True)
        write_runtime_config(config_path, root, scope, hosts)
        written.append(str(config_path))
        write_lock(runtime_lock_path, root, scope=scope, hosts=hosts, profiles=profiles or [])
        written.append(str(runtime_lock_path))
        write_command_shims(root, command_shims)
        written.extend(str(path) for path in command_shims.values())
        for operation in operations:
            destination = operation["destination"]
            source = operation["source"]
            if operation["kind"] == "tree":
                copy_tree(source, destination)
                written.extend(str(path) for path in sorted(destination.rglob("*")) if path.is_file())
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                written.append(str(destination))

    return {
        "kind": "install",
        "status": "planned" if dry_run else "installed",
        "scope": scope,
        "hosts": list(hosts),
        "target": str(base),
        "runtime_root": str(root),
        "version": __version__,
        "config_path": str(config_path),
        "lock_path": str(runtime_lock_path),
        "bin_dir": str(bin_dir),
        "commands": {name: str(path) for name, path in command_shims.items()},
        "dry_run": dry_run,
        "stored_secret": False,
        "planned": planned,
        "written": sorted(set(written)),
        "next_steps": next_steps(scope, hosts),
    }


def resolve_hosts(host: str) -> tuple[str, ...]:
    try:
        return HOST_ALIASES[host]
    except KeyError as exc:
        raise InstallError(f"unsupported host: {host}") from exc


def resolve_base(scope: str, *, target: Path | None, home: Path | None) -> Path:
    if scope == "project":
        return (target or Path.cwd()).resolve()
    configured_home = home or Path(os.environ.get("AIKIT_INSTALL_HOME", str(Path.home())))
    return configured_home.expanduser().resolve()


def build_operations(
    root: Path,
    base: Path,
    hosts: tuple[str, ...],
) -> list[dict[str, Path | str]]:
    operations: list[dict[str, Path | str]] = []
    if "codex" in hosts:
        codex_plugin = root / "plugins" / "codex-ai-devkit"
        codex_skill = codex_plugin / "skills" / "ai-devkit-router"
        operations.extend(
            [
                {
                    "kind": "tree",
                    "source": codex_plugin,
                    "destination": base / ".codex" / "plugins" / "ai-devkit",
                },
                {
                    "kind": "tree",
                    "source": codex_skill,
                    "destination": base / ".codex" / "skills" / "ai-devkit-router",
                },
            ]
        )
    if "claude-code" in hosts:
        claude_plugin = root / "plugins" / "claude-code-ai-devkit"
        claude_skill = claude_plugin / "skills" / "ai-devkit-router"
        claude_commands = claude_plugin / "commands"
        operations.extend(
            [
                {
                    "kind": "tree",
                    "source": claude_plugin,
                    "destination": base / ".claude" / "plugins" / "ai-devkit",
                },
                {
                    "kind": "tree",
                    "source": claude_skill,
                    "destination": base / ".claude" / "skills" / "ai-devkit-router",
                },
                {
                    "kind": "tree",
                    "source": claude_commands,
                    "destination": base / ".claude" / "commands",
                },
            ]
        )
    if "claude-desktop" in hosts:
        claude_desktop_plugin = root / "plugins" / "claude-skill-ai-devkit"
        claude_desktop_skill = claude_desktop_plugin / "ai-devkit"
        operations.extend(
            [
                {
                    "kind": "tree",
                    "source": claude_desktop_plugin,
                    "destination": base / ".claude" / "plugins" / "ai-devkit-skill",
                },
                {
                    "kind": "tree",
                    "source": claude_desktop_skill,
                    "destination": base / ".claude" / "skills" / "ai-devkit",
                },
            ]
        )
    return operations


def validate_sources(operations: list[dict[str, Path | str]]) -> None:
    for operation in operations:
        source = operation["source"]
        if not isinstance(source, Path) or not source.exists():
            raise InstallError(f"install source not found: {source}")


def copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )


def build_command_shims(root: Path, bin_dir: Path) -> dict[str, Path]:
    return {
        "agent": bin_dir / "agent",
        "aikit": bin_dir / "aikit",
        "ai-devkit": bin_dir / "ai-devkit",
    }


def write_command_shims(root: Path, shims: dict[str, Path]) -> None:
    for command, path in shims.items():
        source = root / command
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(command_shim_text(source, root), encoding="utf-8")
        path.chmod(0o755)


def validate_command_sources(root: Path, shims: dict[str, Path]) -> None:
    for command in shims:
        source = root / command
        if not source.exists():
            raise InstallError(f"install command source not found: {source}")


def command_shim_text(source: Path, root: Path) -> str:
    return "\n".join(
        [
            "#!/usr/bin/env sh",
            "set -eu",
            f"export AI_DEVKIT_ROOT={json.dumps(str(root))}",
            f"exec {json.dumps(str(source))} \"$@\"",
            "",
        ]
    )


def write_runtime_config(path: Path, root: Path, scope: str, hosts: tuple[str, ...]) -> None:
    hosts_yaml = "\n".join(f"    - {host}" for host in hosts)
    path.write_text(
        "\n".join(
            [
                "version: 1",
                "runtime:",
                "  source: local",
                f"  root: {json.dumps(str(root))}",
                f"  version: {json.dumps(__version__)}",
                "install:",
                f"  scope: {scope}",
                "  hosts:",
                hosts_yaml,
                "security:",
                "  stored_secret: false",
                "",
            ]
        ),
        encoding="utf-8",
    )


def next_steps(scope: str, hosts: tuple[str, ...]) -> list[str]:
    runtime_dir_name = GLOBAL_RUNTIME_DIR if scope == "global" else PROJECT_RUNTIME_DIR
    steps = [f"Add `{runtime_dir_name}/bin` to PATH when you want to call the installed `agent` directly."]
    steps.append("Run `agent doctor --json` to validate the local runtime.")
    if "codex" in hosts:
        steps.append("Restart or reload Codex so it can discover the AI DevKit plugin/skill.")
    if "claude-code" in hosts:
        steps.append("Restart or reload Claude Code so it can discover the AI DevKit skill and commands.")
    if "claude-desktop" in hosts:
        steps.append("Restart or reload Claude Desktop/Claude.ai so it can discover the AI DevKit skill.")
    if scope == "project":
        steps.append("Commit only the project install artifacts approved by your team; never commit secrets.")
    return steps
