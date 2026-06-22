"""Setup runner for the Figma MCP bridge."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
from typing import Any


AGENT_DIR = Path(__file__).resolve().parents[2]
ROOT = AGENT_DIR.parents[1]
BRIDGE_DIR = AGENT_DIR / "infra" / "integrations" / "figma" / "bin"
BRIDGE_PY = BRIDGE_DIR / "figma-codex-bridge.py"
BRIDGE_SH = BRIDGE_DIR / "figma-codex-bridge"
BRIDGE_CMD = BRIDGE_DIR / "figma-codex-bridge.cmd"


def run() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else ROOT / "docs" / "figma-setup"
        ensure_output_dir(output_dir, args.yes_create_dir)
        codex_status = check_codex(args.codex_command, args.skip_codex_mcp_check)
        login_status = run_login(args.codex_command) if args.login else {"status": "not_requested", "detail": "-"}
        if args.install_bridge:
            install_bridge_files()
        env_values = build_env_values(args)
        write_generated_env(output_dir / "figma-env.generated", env_values)
        if args.write_env:
            update_env_file(Path(args.env_file).expanduser().resolve(), env_values)
        validation = None
        if args.validate_live:
            validation = validate_bridge(args.codex_command)
        report = render_report(args, output_dir, codex_status, login_status, env_values, validation)
        (output_dir / "figma-mcp-setup-report.md").write_text(report, encoding="utf-8")
        print("# Figma MCP Bridge Setup")
        print("")
        print(f"Artefatos gerados em: {output_dir}")
        print(f"Bridge: {BRIDGE_SH if os.name != 'nt' else BRIDGE_CMD}")
        print(f"Codex MCP Figma: {codex_status['status']}")
    except KeyboardInterrupt:
        print("\nOperacao cancelada.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure Figma MCP bridge for figma-ui-ux-product-designer")
    parser.add_argument("--output-dir")
    parser.add_argument("--yes-create-dir", action="store_true")
    parser.add_argument("--install-bridge", action="store_true")
    parser.add_argument("--write-env", action="store_true")
    parser.add_argument("--env-file", default=str(ROOT / ".env"))
    parser.add_argument("--default-plan-key")
    parser.add_argument("--default-project-id")
    parser.add_argument("--codex-command", default=os.environ.get("CODEX_CLI", "codex"))
    parser.add_argument("--skip-codex-mcp-check", action="store_true")
    parser.add_argument("--login", action="store_true", help="executa codex mcp login figma antes da validacao")
    parser.add_argument("--validate-live", action="store_true")
    return parser


def ensure_output_dir(output_dir: Path, yes_create_dir: bool) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"output path exists and is not a directory: {output_dir}")
        return
    if not yes_create_dir:
        print("Posso criar a pasta de setup do Figma MCP neste projeto?")
        print(str(output_dir))
        answer = input("Criar pasta? [s/N] ").strip().lower()
        if answer not in {"s", "sim", "y", "yes"}:
            raise ValueError("criacao da pasta nao autorizada")
    output_dir.mkdir(parents=True, exist_ok=False)


def check_codex(codex_command: str, skip: bool) -> dict[str, str]:
    executable = shlex.split(codex_command)[0]
    resolved = shutil.which(executable) or (executable if Path(executable).exists() else "")
    if not resolved:
        return {"status": "missing", "detail": f"comando nao encontrado: {executable}"}
    if skip:
        return {"status": "skipped", "detail": f"comando encontrado: {resolved}"}
    command = [*shlex.split(codex_command), "mcp", "get", "figma"]
    result = subprocess.run(command, cwd=ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        return {"status": "not_configured", "detail": detail}
    return {"status": "configured", "detail": compact(result.stdout)}


def run_login(codex_command: str) -> dict[str, str]:
    command = [*shlex.split(codex_command), "mcp", "login", "figma"]
    result = subprocess.run(command, cwd=ROOT, check=False, text=True)
    if result.returncode != 0:
        return {"status": "failed", "detail": f"exit code {result.returncode}"}
    return {"status": "completed", "detail": "OAuth concluido pelo Codex CLI"}


def install_bridge_files() -> None:
    missing = [str(path) for path in (BRIDGE_PY, BRIDGE_SH, BRIDGE_CMD) if not path.exists()]
    if missing:
        raise ValueError("arquivos do bridge ausentes: " + ", ".join(missing))
    for path in (BRIDGE_PY, BRIDGE_SH):
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def build_env_values(args: argparse.Namespace) -> dict[str, str]:
    bridge_command = str(BRIDGE_CMD if os.name == "nt" else BRIDGE_SH)
    values = {
        "FIGMA_MCP_ENABLED": "true",
        "FIGMA_DIRECT_MODE": "true",
        "FIGMA_MCP_BRIDGE_COMMAND": quote_env(bridge_command),
        "FIGMA_MCP_BRIDGE_TIMEOUT_SECONDS": "240",
        "FIGMA_DEFAULT_PLAN_KEY": args.default_plan_key or "",
        "FIGMA_DEFAULT_PROJECT_ID": args.default_project_id or "",
    }
    return values


def quote_env(value: str) -> str:
    if any(char.isspace() for char in value):
        return '"' + value.replace('"', '\\"') + '"'
    return value


def write_generated_env(path: Path, values: dict[str, str]) -> None:
    lines = ["# Generated by figma-ui-ux-product-designer/setup-figma-mcp-bridge"]
    lines.extend(f"{key}={value}" for key, value in values.items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_env_file(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines()
    keys = set(values)
    updated: list[str] = []
    seen: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            updated.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in keys:
            updated.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            updated.append(line)
    if not seen:
        if updated and updated[-1].strip():
            updated.append("")
        updated.append("# Figma UI/UX Product Designer")
    for key, value in values.items():
        if key not in seen:
            updated.append(f"{key}={value}")
    path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")


def validate_bridge(codex_command: str) -> dict[str, Any]:
    request = {
        "kind": "figma_mcp_operation",
        "version": "1.0",
        "operation": {
            "capability": "setup-figma-mcp-bridge",
            "action": "diagnose",
        },
    }
    command = [sys.executable, str(BRIDGE_PY), "--codex-command", codex_command]
    result = subprocess.run(
        command,
        cwd=ROOT,
        input=json.dumps(request, ensure_ascii=False),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
    )
    if result.returncode != 0:
        return {"status": "failed", "detail": result.stderr.strip() or result.stdout.strip()}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "failed", "detail": "bridge retornou JSON invalido"}


def render_report(
    args: argparse.Namespace,
    output_dir: Path,
    codex_status: dict[str, str],
    login_status: dict[str, str],
    env_values: dict[str, str],
    validation: dict[str, Any] | None,
) -> str:
    validation_lines = "- Validacao live: nao executada"
    if validation:
        validation_lines = "\n".join(f"- {key}: {value}" for key, value in validation.items())
    env_file = Path(args.env_file).expanduser().resolve()
    return f"""# Figma MCP Bridge Setup Report

## Status

- Codex command: `{args.codex_command}`
- Codex/Figma MCP: `{codex_status['status']}`
- Detail: {codex_status['detail']}
- Login solicitado: {'sim' if args.login else 'nao'}
- Login status: `{login_status['status']}` - {login_status['detail']}
- Bridge instalado: {'sim' if args.install_bridge else 'nao solicitado'}
- `.env` atualizado: {'sim' if args.write_env else 'nao'}
- Env file: `{env_file}`

## Bridge

- Python: `{BRIDGE_PY}`
- macOS/Linux: `{BRIDGE_SH}`
- Windows: `{BRIDGE_CMD}`

## Variaveis Geradas

```env
{env_block(env_values)}
```

## Validacao

{validation_lines}

## Como Usar

```bash
./ai-devkit run figma-ui-ux-product-designer create-web-app-design \\
  --brief demanda.md \\
  --require-direct \\
  --yes-figma-write \\
  --figma-file-name \"Portal\" \\
  --output-dir docs/design/portal \\
  --yes-create-dir
```

Se `codex mcp get figma` falhar, execute `codex mcp login figma` e repita esta
capability com `--validate-live`.
"""


def env_block(values: dict[str, str]) -> str:
    return "\n".join(f"{key}={value}" for key, value in values.items())


def compact(text: str) -> str:
    return " ".join(text.strip().split())[:500] or "-"
