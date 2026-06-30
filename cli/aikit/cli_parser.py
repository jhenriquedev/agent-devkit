"""Argument parser for the public Agent DevKit CLI."""

from __future__ import annotations

import argparse


DETERMINISTIC_COMMANDS = (
    "architecture",
    "roadmap",
    "catalog",
    "plan",
    "route",
    "eval",
    "secret",
    "secrets",
    "agents",
    "capabilities",
    "inspect",
    "run",
    "doctor",
    "commands",
    "onboard",
    "llm",
    "providers",
    "provider",
    "credential",
    "source",
    "memory",
    "shared-memory",
    "personality",
    "setup",
    "alias",
    "session",
    "toolchain",
    "task",
    "scheduler",
    "notifications",
    "calendar",
    "pr",
    "permissions",
    "audit",
    "config",
    "tools",
    "integrations",
    "skills",
    "skill",
    "script",
    "decisions",
    "ollama",
    "local-llm",
    "mcp",
    "local",
    "workflow",
    "team",
    "knowledge",
    "knowledge-base",
    "contribute",
    "contribution",
    "install",
    "wizard",
)
LLM_COMMANDS = ("agent", "execute", "orchestrate")


def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog or "aikit",
        description="AI DevKit CLI",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--dry-run", dest="global_dry_run", action="store_true", help="show execution plan without external write effects")
    parser.add_argument("-v", "--version", action="store_true", help="print CLI version and exit")
    parser.add_argument(
        "-s",
        "--sessions",
        dest="sessions_shortcut",
        action="store_true",
        help="list local conversation sessions and exit",
    )

    subparsers = parser.add_subparsers(dest="command")

    agent_parser = subparsers.add_parser(
        "agent",
        help="handle a natural-language task using an LLM backend",
    )
    agent_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    agent_parser.add_argument("--llm", help="LLM backend id to use")
    agent_parser.add_argument("--dry-run", action="store_true", help="show execution plan without invoking LLM or external writes")
    agent_parser.add_argument("--no-llm-fallback", action="store_true", help="disable automatic fallback to secondary LLM backends")
    agent_parser.add_argument("--session", dest="session_id", help="resume a local conversation session")
    agent_parser.add_argument("--new-session", action="store_true", help="start a new local conversation session")
    agent_parser.add_argument("prompt", nargs=argparse.REMAINDER)

    commands_parser = subparsers.add_parser("commands", help="list CLI command modes")
    commands_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    commands_parser.add_argument("action", nargs="?", default="list", choices=["list"])

    onboard_parser = subparsers.add_parser("onboard", help="inspect startup state and guide first use")
    onboard_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    onboard_parser.add_argument("action", nargs="?", default="show", choices=["show", "minimal", "complete"])

    architecture_parser = subparsers.add_parser("architecture", help="show the Agent DevKit architecture contract")
    architecture_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    architecture_parser.add_argument("action", nargs="?", default="show", choices=["show"])

    roadmap_parser = subparsers.add_parser("roadmap", help="show the deterministic Agent DevKit roadmap")
    roadmap_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    roadmap_parser.add_argument("action", nargs="?", default="show", choices=["show", "phase", "problem"])
    roadmap_parser.add_argument("target", nargs="?")

    catalog_parser = subparsers.add_parser("catalog", help="search and inspect the Agent DevKit catalog")
    catalog_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    catalog_parser.add_argument("action", nargs="?", default="list", choices=["list", "search", "show", "inspect", "rebuild-index"])
    catalog_parser.add_argument("query", nargs="?")
    catalog_parser.add_argument("target", nargs="?")
    catalog_parser.add_argument("--type", dest="item_type")
    catalog_parser.add_argument("--provider")
    catalog_parser.add_argument("--status")
    catalog_parser.add_argument("--write-policy")
    catalog_parser.add_argument("--readiness")

    for command_name, help_text in (
        ("plan", "build an explicit agentic execution plan without executing it"),
        ("execute", "execute a natural-language task through the agentic runtime"),
        ("orchestrate", "orchestrate a natural-language task with planning and review gates"),
    ):
        agentic_parser = subparsers.add_parser(command_name, help=help_text)
        agentic_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        agentic_parser.add_argument("--llm", help="LLM backend id to use")
        agentic_parser.add_argument("--dry-run", action="store_true", help="show execution plan without invoking LLM or external writes")
        agentic_parser.add_argument("--no-llm-fallback", action="store_true", help="disable automatic fallback to secondary LLM backends")
        agentic_parser.add_argument("--session", dest="session_id", help="resume a local conversation session")
        agentic_parser.add_argument("--new-session", action="store_true", help="start a new local conversation session")
        agentic_parser.add_argument("prompt", nargs=argparse.REMAINDER)

    route_parser = subparsers.add_parser("route", help="explain deterministic routing without execution")
    route_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    route_parser.add_argument("action", nargs="?", default="explain", choices=["explain"])
    route_parser.add_argument("prompt", nargs="*")

    eval_parser = subparsers.add_parser("eval", help="run deterministic Agent DevKit eval suites")
    eval_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    eval_parser.add_argument("action", nargs="?", default="list", choices=["list", "run", "report"])
    eval_parser.add_argument("suite", nargs="?")

    secrets_parser = subparsers.add_parser("secrets", help="diagnose secret backends and safe references")
    secrets_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    secrets_parser.add_argument("action", nargs="?", default="doctor", choices=["doctor", "backends", "reference"])
    secrets_parser.add_argument("reference_action", nargs="?", choices=["add", "list", "remove"])
    secrets_parser.add_argument("provider", nargs="?")
    secrets_parser.add_argument("key", nargs="?")
    secrets_parser.add_argument("--env", dest="env")

    secret_parser = subparsers.add_parser("secret", help="manage safe secret references")
    secret_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    secret_parser.add_argument("action", nargs="?", default="doctor", choices=["set", "get", "list", "delete", "doctor"])
    secret_parser.add_argument("provider", nargs="?")
    secret_parser.add_argument("key", nargs="?")
    secret_parser.add_argument("--env", dest="env")
    secret_parser.add_argument("--ref", dest="secret_ref")

    providers_parser = subparsers.add_parser("providers", help="list provider registry entries")
    providers_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    providers_parser.add_argument("action", nargs="?", default="list", choices=["list"])

    provider_parser = subparsers.add_parser("provider", help="inspect or configure one provider")
    provider_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    provider_parser.add_argument("--env-file", action="append", default=[], help="credential env/JSON/YAML file to inspect without printing values")
    provider_parser.add_argument("--env", action="append", default=[], help="persist an environment variable reference for provider configuration")
    provider_parser.add_argument("--from-env", action="store_true", help="persist references for provider fields found in the current environment")
    provider_parser.add_argument("--session-only", action="store_true", help="validate configuration for this invocation without writing config")
    provider_parser.add_argument("action", nargs="?", default="status", choices=["status", "doctor", "configure", "unset"])
    provider_parser.add_argument("provider", nargs="?")

    credential_parser = subparsers.add_parser("credential", help="resolve provider credentials without exposing values")
    credential_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    credential_parser.add_argument("--env-file", action="append", default=[], help="credential env/JSON/YAML file to inspect")
    credential_parser.add_argument("action", nargs="?", default="resolve", choices=["resolve", "backends"])
    credential_parser.add_argument("provider", nargs="?")

    source_parser = subparsers.add_parser("source", help="manage reusable provider/project sources")
    source_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    source_parser.add_argument("action", nargs="?", default="list", choices=["list", "add", "status", "remove"])
    source_parser.add_argument("source_id", nargs="?")
    source_parser.add_argument("--provider", help="provider id used by this source")
    source_parser.add_argument("--label", help="human-readable source label")
    source_parser.add_argument("--config", action="append", default=[], help="source config as KEY=VALUE")
    source_parser.add_argument("--env", action="append", default=[], help="environment reference as PROVIDER_ENV=LOCAL_ENV")
    source_parser.add_argument("--env-file", action="append", default=[], help="credential file reference")
    source_parser.add_argument("--default-for", action="append", default=[], help="intent that should use this source by default")
    source_parser.add_argument("--default-for-agent", action="append", default=[], help="agent id that should use this source by default")
    source_parser.add_argument("--set-default", action="store_true", help="set as default source for its provider")

    wizard_parser = subparsers.add_parser("wizard", help="continue agentic setup wizards")
    wizard_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    wizard_parser.add_argument("action", nargs="?", default="list", choices=["list", "show", "answer", "cancel"])
    wizard_parser.add_argument("wizard_id", nargs="?")
    wizard_parser.add_argument("answer", nargs="*")
    wizard_parser.add_argument("--status", help="filter wizard list by status")
    wizard_parser.add_argument("--no-run", action="store_true", help="do not resume the original prompt after completing a wizard")

    memory_parser = subparsers.add_parser("memory", help="inspect, backup or reset local AI DevKit memory")
    memory_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    memory_parser.add_argument("action", nargs="?", default="show", choices=["show", "path", "reset", "backup", "share", "shared", "read", "submit", "review", "publish"])
    memory_parser.add_argument("memory_id", nargs="?")
    memory_parser.add_argument("submission_id", nargs="?")
    memory_parser.add_argument("--agent", dest="agent_id")
    memory_parser.add_argument("--source", dest="source_id")
    memory_parser.add_argument("--title")
    memory_parser.add_argument("--content")
    memory_parser.add_argument("--key", dest="contributor_key")
    memory_parser.add_argument("--owner-key", dest="owner_key")
    memory_parser.add_argument("--encrypted", action="store_true", help="create an encrypted portable memory backup package")
    memory_parser.add_argument("--passphrase-env", help="environment variable that contains the memory backup passphrase")
    memory_parser.add_argument("--file", dest="backup_file", help="restore a portable memory backup package")
    memory_parser.add_argument("--all", action="store_true", help="reset all local memory")
    memory_parser.add_argument("--sessions", action="store_true", help="reset local conversation sessions")
    memory_parser.add_argument("--tasks", action="store_true", help="reset local task schedules")
    memory_parser.add_argument("--cache", action="store_true", help="reset local cache")
    memory_parser.add_argument("--yes", action="store_true")

    shared_memory_parser = subparsers.add_parser("shared-memory", help="manage owner-reviewed shared memories")
    shared_memory_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    shared_memory_parser.add_argument("action", nargs="?", default="list", choices=["create", "list", "status", "read", "submit", "review", "publish"])
    shared_memory_parser.add_argument("memory_id", nargs="?")
    shared_memory_parser.add_argument("submission_id", nargs="?")
    shared_memory_parser.add_argument("--title")
    shared_memory_parser.add_argument("--content")
    shared_memory_parser.add_argument("--key", dest="contributor_key")
    shared_memory_parser.add_argument("--owner-key", dest="owner_key")
    shared_memory_parser.add_argument("--yes", action="store_true")

    personality_parser = subparsers.add_parser("personality", help="inspect or update local Agent DevKit personality")
    personality_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    personality_parser.add_argument("action", nargs="?", default="show", choices=["show", "edit", "reset"])
    personality_parser.add_argument("--name", dest="agent_name", help="public agent name")
    personality_parser.add_argument("--rename", dest="agent_name", help="rename the local agent")
    personality_parser.add_argument("--user-name", help="user name")
    personality_parser.add_argument("--language", help="default response language")
    personality_parser.add_argument("--tone", help="response tone")
    personality_parser.add_argument("--detail-level", help="response detail level")

    setup_parser = subparsers.add_parser("setup", help="run setup helpers")
    setup_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    setup_parser.add_argument("--dry-run", action="store_true", help="show setup plan without installing external tools")
    setup_parser.add_argument("--yes", action="store_true", help="confirm setup actions")
    setup_parser.add_argument("--set-default", action="store_true", help="make the embedded mini-brain the default LLM")
    setup_parser.add_argument("action", nargs="?", default="plan", choices=["plan", "personality", "mini-brain"])

    alias_parser = subparsers.add_parser("alias", help="manage local command aliases for agent")
    alias_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    alias_parser.add_argument("action", nargs="?", default="list", choices=["add", "list", "remove", "sync"])
    alias_parser.add_argument("name", nargs="?")
    alias_parser.add_argument("--force", action="store_true", help="allow replacing an existing local alias file")

    session_parser = subparsers.add_parser("session", help="manage local conversation sessions")
    session_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    session_parser.add_argument("action", nargs="?", default="list", choices=["list", "show", "resume"])
    session_parser.add_argument("session_id", nargs="?")

    toolchain_parser = subparsers.add_parser("toolchain", help="inspect or install external tools")
    toolchain_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    toolchain_parser.add_argument("action", nargs="?", default="list", choices=["list", "doctor", "install"])
    toolchain_parser.add_argument("tool", nargs="?", default="all")
    toolchain_parser.add_argument("--dry-run", action="store_true", help="show install plan without executing it")
    toolchain_parser.add_argument("--yes", action="store_true", help="confirm external tool installation")

    task_parser = subparsers.add_parser("task", help="manage local scheduled tasks")
    task_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    task_parser.add_argument("action", nargs="?", default="list", choices=["create", "list", "show", "history", "run", "pause", "resume", "update", "enable", "disable", "delete"])
    task_parser.add_argument("task_id", nargs="?")
    task_parser.add_argument("--title")
    task_parser.add_argument("--prompt")
    task_parser.add_argument("--every")
    task_parser.add_argument("--cron")
    task_parser.add_argument("--dry-run", action="store_true")
    task_parser.add_argument("--yes", action="store_true")

    scheduler_parser = subparsers.add_parser("scheduler", help="run local scheduler")
    scheduler_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    scheduler_parser.add_argument("action", nargs="?", default="run-once", choices=["run-once", "daemon"])
    scheduler_parser.add_argument("--dry-run", action="store_true")

    notifications_parser = subparsers.add_parser("notifications", help="manage local notifications")
    notifications_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    notifications_parser.add_argument(
        "action",
        nargs="?",
        default="doctor",
        choices=["doctor", "send", "format", "configure", "configure-channel", "list-events", "list-channels"],
    )
    notifications_parser.add_argument("--title", default="Agent DevKit")
    notifications_parser.add_argument("--message")
    notifications_parser.add_argument("--summary")
    notifications_parser.add_argument("--event", default="task.completed")
    notifications_parser.add_argument("--status")
    notifications_parser.add_argument("--severity", default="info")
    notifications_parser.add_argument("--task-id")
    notifications_parser.add_argument("--origin", default="cli")
    notifications_parser.add_argument("--enabled", choices=["true", "false"])
    notifications_parser.add_argument("--event-filter", action="append", default=[])
    notifications_parser.add_argument("--artifact", action="append", default=[])
    notifications_parser.add_argument("--next-step", action="append", default=[])
    notifications_parser.add_argument("--channel", action="append", default=[])
    notifications_parser.add_argument("--sensitive", action="store_true")

    calendar_parser = subparsers.add_parser("calendar", help="inspect configured calendar")
    calendar_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    calendar_parser.add_argument("action", nargs="?", default="today", choices=["today", "tomorrow", "list", "configure"])
    calendar_parser.add_argument("--from", dest="date_from")
    calendar_parser.add_argument("--to", dest="date_to")
    calendar_parser.add_argument("--ics")
    calendar_parser.add_argument("--timezone")

    pr_parser = subparsers.add_parser("pr", help="review GitHub pull requests")
    pr_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    pr_parser.add_argument("action", nargs="?", default="list-review-requests", choices=["list-review-requests", "inspect", "review", "automation"])
    pr_parser.add_argument("pr_ref", nargs="?")
    pr_parser.add_argument("automation_action", nargs="?")
    pr_parser.add_argument("--approve", action="store_true")
    pr_parser.add_argument("--request-changes", action="store_true")
    pr_parser.add_argument("--comment")
    pr_parser.add_argument("--allow-write", action="store_true")
    pr_parser.add_argument("--dry-run", action="store_true")
    pr_parser.add_argument("--time", default="09:00")

    permissions_parser = subparsers.add_parser("permissions", help="manage local permission policies")
    permissions_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    permissions_parser.add_argument("action", nargs="?", default="show", choices=["show", "grant", "revoke"])
    permissions_parser.add_argument("agent", nargs="?")
    permissions_parser.add_argument("provider", nargs="?")
    permissions_parser.add_argument("level", nargs="?")
    permissions_parser.add_argument("--project")
    permissions_parser.add_argument("--task", dest="task_id")

    audit_parser = subparsers.add_parser("audit", help="inspect local execution audit trail")
    audit_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    audit_parser.add_argument("action", nargs="?", default="list", choices=["list", "show", "export"])
    audit_parser.add_argument("execution_id", nargs="?")
    audit_parser.add_argument("--limit", type=int, default=20)
    audit_parser.add_argument("--format", default="md", choices=["md", "json"])

    config_parser = subparsers.add_parser("config", help="inspect local Agent DevKit configuration")
    config_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    config_parser.add_argument("action", nargs="?", default="show", choices=["show", "path", "migrate-home"])
    config_parser.add_argument("--dry-run", action="store_true", help="plan home migration without moving files")

    for command_name, help_text in (
        ("tools", "manage enabled local tools"),
        ("integrations", "manage provider integration decisions"),
        ("skills", "manage local skill decisions"),
    ):
        control_parser = subparsers.add_parser(command_name, help=help_text)
        control_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        control_parser.add_argument("action", nargs="?", default="list", choices=["list", "enable", "disable"])
        control_parser.add_argument("item_id", nargs="?")

    decisions_parser = subparsers.add_parser("decisions", help="inspect or reset local opt-in and opt-out decisions")
    decisions_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    decisions_parser.add_argument("action", nargs="?", default="list", choices=["list", "forget", "reset"])
    decisions_parser.add_argument("item_id", nargs="?")
    decisions_parser.add_argument("--category", choices=["tools", "integrations", "skills", "llms"])

    mcp_parser = subparsers.add_parser("mcp", help="serve Agent DevKit as a MCP stdio server")
    mcp_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    mcp_parser.add_argument("action", nargs="?", default="manifest", choices=["manifest", "tools", "doctor", "serve"])

    ollama_parser = subparsers.add_parser("ollama", help="inspect and manage local Ollama models")
    ollama_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    ollama_parser.add_argument("action", nargs="?", default="status", choices=["status", "models", "pull", "update"])
    ollama_parser.add_argument("model", nargs="?")
    ollama_parser.add_argument("--yes", action="store_true", help="confirm Ollama model or update operation")
    ollama_parser.add_argument("--dry-run", action="store_true", help="show Ollama operation without executing it")

    local_llm_parser = subparsers.add_parser("local-llm", help="inspect and manage local LLM workers")
    local_llm_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    local_llm_parser.add_argument("action", nargs="?", default="list", choices=["list", "doctor", "models", "install", "remove", "benchmark"])
    local_llm_parser.add_argument("model", nargs="?")
    local_llm_parser.add_argument("--yes", action="store_true", help="confirm local model operation")
    local_llm_parser.add_argument("--dry-run", action="store_true", help="show local model operation without executing it")

    llm_parser = subparsers.add_parser("llm", help="manage LLM backends")
    llm_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    llm_parser.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["list", "doctor", "configure", "set-default", "default", "enable", "disable", "preference"],
    )
    llm_parser.add_argument("backend", nargs="?")
    llm_parser.add_argument("preference_value", nargs="?")
    llm_parser.add_argument("--api-key-env", help="environment variable that stores the API key")
    llm_parser.add_argument("--base-url", help="OpenAI-compatible base URL")
    llm_parser.add_argument("--model", help="default model id")
    llm_parser.add_argument("--command", dest="host_command", help="host CLI command name or path")
    llm_parser.add_argument("--set-default", action="store_true", help="set backend as the default LLM")
    llm_parser.add_argument("--primary", help="primary backend for LLM preference")
    llm_parser.add_argument("--order", help="comma-separated fallback order")

    install_parser = subparsers.add_parser("install", help="install AI DevKit host artifacts")
    install_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    install_parser.add_argument("scope", nargs="?", default="project", choices=["project", "global"])
    install_parser.add_argument("--target", help="project directory for project installs")
    install_parser.add_argument("--home", help="home directory override for global installs")
    install_parser.add_argument(
        "--host",
        default="all",
        choices=["all", "codex", "claude-code", "claude-desktop", "claude-ai"],
        help="host adapter to install",
    )
    install_parser.add_argument("--profiles", help="comma-separated project profiles to record in the lock")
    install_parser.add_argument("--dry-run", action="store_true", help="print planned writes without creating files")

    agents_parser = subparsers.add_parser("agents", aliases=["a"], help="list, search or inspect available agents")
    agents_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    agents_parser.add_argument("action", nargs="?", default="list", choices=["list", "search", "show", "create", "validate", "local-list"])
    agents_parser.add_argument("query", nargs="?")
    agents_parser.add_argument("--description")
    agents_parser.add_argument("--force", action="store_true")

    capabilities_parser = subparsers.add_parser(
        "capabilities",
        aliases=["c"],
        help="list capabilities",
    )
    capabilities_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    capabilities_parser.add_argument("action_or_agent", nargs="?", default="list")
    capabilities_parser.add_argument("legacy_agent", nargs="?")
    capabilities_parser.add_argument("show_capability", nargs="?")
    capabilities_parser.add_argument("--agent", dest="agent")

    local_parser = subparsers.add_parser("local", help="manage local Agent DevKit extensions")
    local_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    local_parser.add_argument("action", nargs="?", default="list", choices=["list", "add", "disable", "enable", "remove", "validate", "automation", "agents", "agent"])
    local_parser.add_argument("extension_id", nargs="?")
    local_parser.add_argument("local_item_id", nargs="?")
    local_parser.add_argument("--path")
    local_parser.add_argument("--title")
    local_parser.add_argument("--prompt")
    local_parser.add_argument("--command", dest="local_command")
    local_parser.add_argument("--every")
    local_parser.add_argument("--cron")
    local_parser.add_argument("--force", action="store_true")
    local_parser.add_argument("--yes", action="store_true")

    skill_parser = subparsers.add_parser("skill", help="create and manage local Agent DevKit skills")
    skill_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    skill_parser.add_argument("action", nargs="?", default="list", choices=["create", "list", "show", "update", "delete"])
    skill_parser.add_argument("skill_id", nargs="?")
    skill_parser.add_argument("--description")
    skill_parser.add_argument("--force", action="store_true")
    skill_parser.add_argument("--yes", action="store_true")

    script_parser = subparsers.add_parser("script", help="create and run local scripts")
    script_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    script_parser.add_argument("action", nargs="?", default="list", choices=["create", "list", "run"])
    script_parser.add_argument("script_id", nargs="?")
    script_parser.add_argument("--command", dest="script_command")
    script_parser.add_argument("--force", action="store_true")
    script_parser.add_argument("--dry-run", action="store_true")
    script_parser.add_argument("--yes", action="store_true")

    workflow_parser = subparsers.add_parser("workflow", help="list, install or run installable workflows")
    workflow_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    workflow_parser.add_argument("action", nargs="?", default="list", choices=["list", "show", "install", "run"])
    workflow_parser.add_argument("workflow_id", nargs="?")
    workflow_parser.add_argument("--dry-run", action="store_true")
    workflow_parser.add_argument("--yes", action="store_true")

    team_parser = subparsers.add_parser("team", help="manage project-local team profiles")
    team_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    team_parser.add_argument("action", nargs="?", default="status", choices=["init", "status", "doctor", "onboard", "profile"])
    team_parser.add_argument("profile_action", nargs="?", choices=["list", "show", "use", "export", "import"])
    team_parser.add_argument("profile_id", nargs="?")
    team_parser.add_argument("--path", dest="profile_path")
    team_parser.add_argument("--force", action="store_true")

    knowledge_parser = subparsers.add_parser("knowledge", help="manage file-first shared knowledge bases")
    knowledge_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    knowledge_parser.add_argument(
        "action",
        nargs="?",
        default="doctor",
        choices=["init", "doctor", "search", "index", "reindex", "snapshot", "review", "curate", "publish", "sync"],
    )
    knowledge_parser.add_argument("target", nargs="?")
    knowledge_parser.add_argument("snapshot_action", nargs="?")
    knowledge_parser.add_argument("--title")
    knowledge_parser.add_argument("--content")
    knowledge_parser.add_argument("--from-file")
    knowledge_parser.add_argument("--type", dest="entry_type")
    knowledge_parser.add_argument("--owner-agent")
    knowledge_parser.add_argument("--force", action="store_true")
    knowledge_parser.add_argument("--yes", action="store_true")

    knowledge_base_parser = subparsers.add_parser("knowledge-base", help="manage file-first shared knowledge bases")
    knowledge_base_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    knowledge_base_parser.add_argument(
        "action",
        nargs="?",
        default="status",
        choices=["create", "join", "status", "tokens", "rotate-token"],
    )
    knowledge_base_parser.add_argument("target", nargs="?")
    knowledge_base_parser.add_argument("--provider", default="local")
    knowledge_base_parser.add_argument("--force", action="store_true")

    for contribution_command in ("contribute", "contribution"):
        contribution_parser = subparsers.add_parser(contribution_command, help="prepare or review local extension contributions")
        contribution_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        contribution_parser.add_argument(
            "action",
            nargs="?",
            default="list" if contribution_command == "contribute" else "checklist",
            choices=["list", "prepare", "validate", "review", "checklist", "pr"],
        )
        contribution_parser.add_argument("extension_id", nargs="?")
        contribution_parser.add_argument("--dry-run", action="store_true")
        contribution_parser.add_argument("--yes", action="store_true")

    inspect_parser = subparsers.add_parser(
        "inspect",
        aliases=["i"],
        help="inspect an agent capability",
    )
    inspect_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    inspect_parser.add_argument("agent")
    inspect_parser.add_argument("capability")

    run_parser = subparsers.add_parser(
        "run",
        aliases=["r"],
        help="run an agent capability",
    )
    run_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    run_parser.add_argument("agent")
    run_parser.add_argument("capability")
    run_parser.add_argument("capability_args", nargs=argparse.REMAINDER)

    doctor_parser = subparsers.add_parser("doctor", help="run local diagnostics")
    doctor_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    doctor_parser.add_argument("--scope", default="auto", choices=["auto", "project", "global"], help="diagnostic scope")
    doctor_parser.add_argument("--project", help="project directory whose AI DevKit lock should be checked")
    doctor_parser.add_argument("--home", help="home directory override for global lock checks")
    return parser
