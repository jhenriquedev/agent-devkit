"""Agent/capability registry and execution runtime."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from cli.aikit.agent_registry import normalize_agent_mode, normalize_source_contract
from cli.aikit.configuration_orchestrator import provider_wizard_from_requirement
from cli.aikit.core.capability_contract import capability_policy
from cli.aikit.errors import DevKitError
from cli.aikit.fallback import evaluate_provider_requirements
from cli.aikit.guardrails import evaluate_execution_guardrails
from cli.aikit.output import run_payload
from cli.aikit.runtime_paths import AGENTS_DIR, ROOT
from cli.aikit.setup_wizard_payload import persist_setup_wizard_payload
from cli.aikit.sources import (
    SourceRegistryError,
    apply_source_to_args,
    extract_source_arg,
    resolve_source,
    source_env,
)
from cli.aikit.write_policy import normalize_write_policy, write_policy_public_fields


def resolve_capabilities_agent(args: argparse.Namespace) -> str | None:
    if args.agent:
        return args.agent

    action_or_agent = args.action_or_agent
    if action_or_agent == "list":
        return args.legacy_agent

    # Backward compatibility: `ai-devkit capabilities <agent>`.
    if args.legacy_agent:
        raise DevKitError("unexpected extra argument for capabilities")
    return action_or_agent


def runner_timeout_seconds() -> int:
    raw = os.environ.get("AI_DEVKIT_RUN_TIMEOUT", "300")
    return int(raw) if raw.isdigit() and int(raw) > 0 else 300


def list_agents() -> list[dict[str, Any]]:
    if not AGENTS_DIR.exists():
        return []

    agents = []
    for path in sorted(AGENTS_DIR.iterdir()):
        if not path.is_dir():
            continue
        manifest = path / "agent.yaml"
        if not manifest.exists():
            continue
        data = load_manifest(manifest)
        capabilities = list_capabilities(path)
        agents.append(
            {
                "id": data.get("id", path.name),
                "name": data.get("name", path.name),
                "status": data.get("status"),
                "version": data.get("version"),
                "path": str(path.relative_to(ROOT)),
                "purpose": compact_text(data.get("purpose")),
                "agent_mode": normalize_agent_mode(data.get("agent_mode")),
                "capabilities": len(capabilities),
            }
        )
    return agents


def load_agent(agent_id: str) -> dict[str, Any]:
    path = AGENTS_DIR / agent_id
    manifest = path / "agent.yaml"
    if not manifest.exists():
        available = ", ".join(item["id"] for item in list_agents()) or "none"
        raise DevKitError(f"agent not found: {agent_id}. available: {available}")

    data = load_manifest(manifest)
    data["path"] = path
    data["manifest_path"] = manifest
    return data


def summarize_agent(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": agent.get("id"),
        "name": agent.get("name"),
        "status": agent.get("status"),
        "version": agent.get("version"),
        "path": str(agent["path"].relative_to(ROOT)),
        "agent_mode": normalize_agent_mode(agent.get("agent_mode")),
    }


def list_all_capabilities() -> list[dict[str, Any]]:
    capabilities: list[dict[str, Any]] = []
    for agent in list_agents():
        agent_path = AGENTS_DIR / agent["id"]
        for capability in list_capabilities(agent_path):
            item = dict(capability)
            item["agent"] = agent["id"]
            capabilities.append(item)
    return capabilities


def list_capabilities(agent_path: Path) -> list[dict[str, Any]]:
    capabilities_dir = agent_path / "capabilities"
    if not capabilities_dir.exists():
        return []

    capabilities = []
    for path in sorted(capabilities_dir.iterdir()):
        if not path.is_dir():
            continue
        manifest = path / "capability.yaml"
        if not manifest.exists():
            continue
        data = load_manifest(manifest)
        runner = ((data.get("entrypoint", {}) or {}).get("runner"))
        capabilities.append(
            {
                "id": data.get("id", path.name),
                "name": data.get("name", path.name),
                "status": data.get("status"),
                "version": data.get("version"),
                "path": str(path.relative_to(ROOT)),
                "purpose": compact_text(data.get("purpose")),
                "source": normalize_source_contract(data.get("source"), runtime=data.get("runtime")),
                "source_contract": normalize_source_contract(data.get("source"), runtime=data.get("runtime")),
                "write_policy": normalize_write_policy(data.get("write_policy")),
                "write_policy_raw": data.get("write_policy"),
                **write_policy_public_fields(data.get("write_policy")),
                "runner": runner,
                "has_runner": bool(runner),
                "has_workflow": (path / "workflow.md").exists(),
                "has_decision_rules": (path / "decision-rules.md").exists(),
            }
        )
    return capabilities


def load_capability(agent_path: Path, capability_id: str) -> dict[str, Any]:
    path = agent_path / "capabilities" / capability_id
    manifest = path / "capability.yaml"
    if not manifest.exists():
        available = ", ".join(item["id"].split(".")[-1] for item in list_capabilities(agent_path))
        raise DevKitError(
            f"capability not found: {capability_id}. available: {available or 'none'}"
        )

    data = load_manifest(manifest)
    return {
        "id": data.get("id", capability_id),
        "name": data.get("name", capability_id),
        "status": data.get("status"),
        "version": data.get("version"),
        "path": str(path.relative_to(ROOT)),
        "purpose": compact_text(data.get("purpose")),
        "inputs": data.get("inputs", {}),
        "outputs": data.get("outputs", {}),
        "entrypoint": resolve_refs(path, data.get("entrypoint", {})),
        "integration": resolve_integration_refs(path, data.get("integration", {})),
        "runtime": data.get("runtime", {}) if isinstance(data.get("runtime"), dict) else {},
        "source": normalize_source_contract(data.get("source"), runtime=data.get("runtime")),
        "source_contract": normalize_source_contract(data.get("source"), runtime=data.get("runtime")),
        "requires": data.get("requires", {}) if isinstance(data.get("requires"), dict) else {},
        "write_policy": normalize_write_policy(data.get("write_policy")),
        "write_policy_raw": data.get("write_policy"),
        **write_policy_public_fields(data.get("write_policy")),
    }


def run_capability(
    agent: dict[str, Any],
    capability_id: str,
    capability_args: list[str],
    capture_output: bool = True,
    *,
    origin: str = "core",
    request_id: str | None = None,
    request_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    agent_path = agent["path"]
    capability_path = agent_path / "capabilities" / capability_id
    manifest = capability_path / "capability.yaml"
    if not manifest.exists():
        available = ", ".join(item["id"].split(".")[-1] for item in list_capabilities(agent_path))
        raise DevKitError(
            f"capability not found: {capability_id}. available: {available or 'none'}"
        )

    data = load_manifest(manifest)
    run_metadata = {
        "origin": origin,
        "request_id": request_id,
        "data": request_data or {},
        "policy": capability_policy(data),
    }
    try:
        source = None
        source_contract = runtime_source_contract(data)
        if supports_runtime_source(data):
            source_id, capability_args = extract_source_arg(capability_args)
            source = resolve_source(source_id=source_id) if source_id else None
            capability_args = apply_source_to_args(source, source_contract, capability_args)
        runtime_env = os.environ | source_env(source, source_contract)
    except SourceRegistryError as exc:
        return run_payload(
            status="blocked",
            agent=summarize_agent(agent),
            capability=data.get("id", capability_id),
            runner=None,
            returncode=2,
            error=str(exc),
            reason="source_resolution_failed",
            risks=["Source configuration could not be resolved."],
            next_steps=["Inspect available sources with `agent source list` or configure one with `agent source add`."],
            exit_code=2,
            **run_metadata,
        )
    guardrail = evaluate_execution_guardrails(data, capability_args)
    capability_args = guardrail["args"]
    if not guardrail["ready"]:
        return run_payload(
            status="blocked",
            agent=summarize_agent(agent),
            capability=data.get("id", capability_id),
            runner=None,
            returncode=2,
            guardrail={
                "reason": guardrail["reason"],
                "write_policy": guardrail["write_policy"],
                "execute_requested": True,
            },
            reason=guardrail["reason"],
            risks=guardrail["risks"],
            next_steps=guardrail["next_steps"],
            exit_code=2,
            **run_metadata,
        )
    readiness = evaluate_provider_requirements(ROOT, data, capability_args)
    if not readiness["ready"]:
        payload = run_payload(
            status=readiness["status"],
            agent=summarize_agent(agent),
            capability=data.get("id", capability_id),
            runner=None,
            returncode=readiness.get("exit_code") or 0,
            providers=readiness["providers"],
            fallback_applied=readiness["fallback_applied"],
            evidence=readiness["evidence"],
            risks=readiness["risks"],
            next_steps=readiness["next_steps"],
            artifacts=readiness["artifacts"],
            reason="provider_not_ready",
            exit_code=readiness.get("exit_code"),
            **run_metadata,
        )
        wizard = setup_wizard_from_readiness(readiness, agent=summarize_agent(agent), capability_id=str(data.get("id", capability_id)))
        if wizard:
            payload["setup_wizard"] = wizard
            payload["next_question"] = wizard.get("next_question")
            payload["configuration_agent"] = wizard.get("owner_agent")
            payload["next_steps"] = [
                "Responda a pergunta do wizard para autorizar ou negar a configuracao deste provider.",
                "Informe uma referencia segura de credencial por variavel de ambiente, arquivo ou cadeia nativa quando solicitado.",
                "Reexecute ou retome a mesma capability depois que a configuracao estiver salva.",
            ]
            payload = persist_setup_wizard_payload(payload)
        return payload

    runner_ref = (data.get("entrypoint", {}) or {}).get("runner")
    if not runner_ref:
        if capture_output:
            return run_payload(
                status="failed",
                agent=summarize_agent(agent),
                capability=data.get("id", capability_id),
                runner=None,
                returncode=2,
                providers=readiness["providers"],
                error=f"capability has no runner: {capability_id}",
                reason="missing_runner",
                risks=["Capability cannot be executed by the runtime because no runner is declared."],
                next_steps=["Add `entrypoint.runner` to the capability manifest or use a capability with an executable runner."],
                exit_code=2,
                **run_metadata,
            )
        raise DevKitError(f"capability has no runner: {capability_id}")

    runner_path = (capability_path / runner_ref).resolve()
    if not runner_path.exists():
        if capture_output:
            relative_runner = str(runner_path.relative_to(ROOT))
            return run_payload(
                status="failed",
                agent=summarize_agent(agent),
                capability=data.get("id", capability_id),
                runner=relative_runner,
                returncode=2,
                providers=readiness["providers"],
                error=f"runner not found: {relative_runner}",
                reason="runner_not_found",
                risks=["Capability runner declared in the manifest does not exist on disk."],
                next_steps=["Fix `entrypoint.runner` in the capability manifest or restore the missing runner file."],
                exit_code=2,
                **run_metadata,
            )
        raise DevKitError(f"runner not found: {runner_path.relative_to(ROOT)}")

    timeout_seconds = runner_timeout_seconds()
    try:
        if capture_output:
            process = subprocess.run(
                [sys.executable, str(runner_path), *capability_args],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=runtime_env,
                timeout=timeout_seconds,
            )
        else:
            process = subprocess.run(
                [sys.executable, str(runner_path), *capability_args],
                cwd=ROOT,
                check=False,
                text=True,
                env=runtime_env,
                timeout=timeout_seconds,
            )
    except subprocess.TimeoutExpired as exc:
        if capture_output:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
            return run_payload(
                status="failed",
                agent=summarize_agent(agent),
                capability=data.get("id", capability_id),
                runner=str(runner_path.relative_to(ROOT)),
                stdout=stdout,
                stderr=stderr,
                returncode=124,
                providers=readiness["providers"],
                error=f"runner timed out after {timeout_seconds}s: {agent.get('id')}/{capability_id}",
                reason="runner_timeout",
                risks=["Capability runner exceeded the configured timeout."],
                next_steps=["Review runner performance, inputs, provider latency, or increase `AI_DEVKIT_RUN_TIMEOUT` for this execution."],
                exit_code=124,
                **run_metadata,
            )
        raise DevKitError(f"runner timed out after {timeout_seconds}s: {agent.get('id')}/{capability_id}") from exc
    if process.returncode != 0:
        stderr = process.stderr if capture_output else ""
        if capture_output:
            stdout = process.stdout or ""
            message = (stderr or stdout or f"runner failed: {process.returncode}").strip()
            return run_payload(
                status="failed",
                agent=summarize_agent(agent),
                capability=data.get("id", capability_id),
                runner=str(runner_path.relative_to(ROOT)),
                stdout=stdout,
                stderr=stderr,
                returncode=process.returncode,
                providers=readiness["providers"],
                error=message,
                reason="runner_failed",
                risks=["Capability runner returned a non-zero exit code."],
                next_steps=["Review stdout/stderr and rerun after correcting the capability inputs or environment."],
                exit_code=process.returncode,
                **run_metadata,
            )
        raise DevKitError((stderr or "").strip() or f"runner failed: {process.returncode}")

    return run_payload(
        status="ok",
        agent=summarize_agent(agent),
        capability=data.get("id", capability_id),
        runner=str(runner_path.relative_to(ROOT)),
        stdout=process.stdout if capture_output else "",
        stderr=process.stderr if capture_output else "",
        returncode=process.returncode,
        providers=readiness["providers"],
        **run_metadata,
    )


def supports_runtime_source(capability: dict[str, Any]) -> bool:
    source = runtime_source_contract(capability)
    return bool(source.get("enabled"))


def runtime_source_contract(capability: dict[str, Any]) -> dict[str, Any]:
    runtime = capability.get("runtime") if isinstance(capability.get("runtime"), dict) else {}
    return normalize_source_contract(capability.get("source"), runtime=runtime)


def setup_wizard_from_readiness(readiness: dict[str, Any], *, agent: dict[str, Any], capability_id: str) -> dict[str, Any] | None:
    providers = readiness.get("providers") if isinstance(readiness.get("providers"), dict) else {}
    missing = providers.get("missing") or []
    if not missing:
        return None
    provider_id = str(missing[0])
    details = providers.get("details") or []
    detail = next((item for item in details if isinstance(item, dict) and item.get("id") == provider_id), {})
    try:
        return provider_wizard_from_requirement(
            ROOT,
            provider_id,
            agent_id=str(agent.get("id") or ""),
            capability_id=capability_id,
            reason=str(detail.get("purpose") or "Provider is required but not configured."),
        )
    except Exception:
        return None



def resolve_refs(base: Path, refs: dict[str, Any]) -> dict[str, Any]:
    resolved = {}
    for key, value in refs.items():
        if isinstance(value, str):
            resolved[key] = {
                "ref": value,
                "path": str((base / value).resolve().relative_to(ROOT)),
                "exists": (base / value).resolve().exists(),
            }
        else:
            resolved[key] = value
    return resolved


def resolve_integration_refs(base: Path, integration: dict[str, Any]) -> dict[str, Any]:
    if not integration:
        return {}

    resolved: dict[str, Any] = {}
    repository = integration.get("repository")
    if repository:
        repository_path = (base / repository).resolve()
        resolved["repository"] = {
            "ref": repository,
            "path": str(repository_path.relative_to(ROOT)),
            "exists": repository_path.exists(),
        }

    methods = []
    for method in integration.get("methods", []) or []:
        method_path = (base / method).resolve()
        methods.append(
            {
                "ref": method,
                "path": str(method_path.relative_to(ROOT)),
                "exists": method_path.exists(),
            }
        )
    resolved["methods"] = methods
    return resolved


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return load_simple_yaml(path)

    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise DevKitError(f"manifest must be a mapping: {path}")
    return data


def load_simple_yaml(path: Path) -> dict[str, Any]:
    # Fallback parser for simple top-level YAML used by the CLI when PyYAML is
    # unavailable. It is intentionally narrow; install PyYAML for full support.
    data: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            if value:
                data[current_key] = parse_scalar(value)
                current_list = None
            else:
                current_list = []
                data[current_key] = current_list
            continue
        if current_key and current_list is not None and stripped.startswith("- "):
            current_list.append(stripped[2:].strip())
    return data


def parse_scalar(value: str) -> Any:
    if value in {"true", "false"}:
        return value == "true"
    return value.strip('"').strip("'")


def compact_text(value: Any) -> str | None:
    if value is None:
        return None
    return " ".join(str(value).split())
