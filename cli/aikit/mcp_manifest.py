"""MCP manifest and tool schemas for Agent DevKit."""

from __future__ import annotations

from typing import Any

from cli.aikit import __version__


MCP_PROTOCOL_VERSION = "2025-11-25"
MCP_SERVER_NAME = "agent-devkit"


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "agent_devkit_agents_list",
        "description": "List available Agent DevKit agents.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_capabilities_list",
        "description": "List available capabilities, optionally filtered by agent id.",
        "inputSchema": {
            "type": "object",
            "properties": {"agent_id": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_capability_inspect",
        "description": "Inspect one capability contract.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "capability_id": {"type": "string"},
            },
            "required": ["agent_id", "capability_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_capability_run",
        "description": "Run a read-only capability or dry-run a non-read-only capability through Agent DevKit core.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "capability_id": {"type": "string"},
                "args": {"type": "array", "items": {"type": "string"}},
                "inputs": {"type": "object"},
                "source_id": {"type": "string"},
                "dry_run": {"type": "boolean"},
                "request_id": {"type": "string"},
            },
            "required": ["agent_id", "capability_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_doctor",
        "description": "Return local Agent DevKit diagnostics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "home": {"type": "string"},
                "scope": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_onboarding_status",
        "description": "Return the no-argument Agent DevKit onboarding status used by `agent` startup.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_memory_show",
        "description": "Show local Agent DevKit memory usage and memory file paths without exposing secrets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "source_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_memory_path",
        "description": "Ensure local memory files exist and return their paths.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_memory_reset",
        "description": "Reset local Agent DevKit memory, sessions, tasks or cache. This is a local-only write.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "all": {"type": "boolean"},
                "agent_id": {"type": "string"},
                "source_id": {"type": "string"},
                "sessions": {"type": "boolean"},
                "tasks": {"type": "boolean"},
                "cache": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_memory_backup_create",
        "description": "Create a local backup of Agent DevKit memory and personality. This does not upload remotely.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "encrypted": {"type": "boolean"},
                "passphrase_env": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_memory_backup_list",
        "description": "List local Agent DevKit memory backups.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_memory_backup_restore",
        "description": "Restore a local Agent DevKit memory backup. Requires yes=true to execute.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "backup_id": {"type": "string"},
                "file": {"type": "string"},
                "passphrase_env": {"type": "string"},
                "yes": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_memory_backup_delete",
        "description": "Delete a local Agent DevKit memory backup. Requires yes=true to execute.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "backup_id": {"type": "string"},
                "yes": {"type": "boolean"},
            },
            "required": ["backup_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_shared_memory_list",
        "description": "List owner-reviewed shared memories stored in the local Agent DevKit home.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_shared_memory_status",
        "description": "Inspect one owner-reviewed shared memory workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {"memory_id": {"type": "string"}},
            "required": ["memory_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_shared_memory_create",
        "description": "Create a local shared memory workspace and contributor key. This is a local-only write.",
        "inputSchema": {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_shared_memory_read",
        "description": "Read accepted shared memory entries without exposing owner keys.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string"},
                "entry_id": {"type": "string"},
                "key": {"type": "string"},
            },
            "required": ["memory_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_shared_memory_submit",
        "description": "Submit a contribution to shared memory pending owner review. This is a local-only write.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "key": {"type": "string"},
            },
            "required": ["memory_id", "content", "key"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_shared_memory_review",
        "description": "Review a pending shared memory contribution without publishing it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string"},
                "submission_id": {"type": "string"},
            },
            "required": ["memory_id", "submission_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_shared_memory_publish",
        "description": "Publish an approved shared memory contribution. This is a local-only write.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string"},
                "submission_id": {"type": "string"},
                "yes": {"type": "boolean"},
                "owner_key": {"type": "string"},
            },
            "required": ["memory_id", "submission_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_personality_show",
        "description": "Show the local Agent DevKit personality and public identity.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_personality_update",
        "description": "Update local Agent DevKit personality fields. This is a local-only write.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string"},
                "user_name": {"type": "string"},
                "language": {"type": "string"},
                "tone": {"type": "string"},
                "detail_level": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_personality_reset",
        "description": "Reset local Agent DevKit personality to defaults. This is a local-only write.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_task_list",
        "description": "List local scheduled tasks without running them.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_task_show",
        "description": "Show one local scheduled task.",
        "inputSchema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_task_run_dry_run",
        "description": "Preview one local scheduled task run without executing it.",
        "inputSchema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_scheduler_run_once_dry_run",
        "description": "Preview due local scheduled tasks without executing them.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_notifications_doctor",
        "description": "Diagnose local notification support without sending notifications.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_notifications_list_events",
        "description": "List supported local notification events.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_notifications_list_channels",
        "description": "List supported and future notification channels.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_notifications_format",
        "description": "Format a notification payload without sending it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "message": {"type": "string"},
                "summary": {"type": "string"},
                "event": {"type": "string"},
                "status": {"type": "string"},
                "severity": {"type": "string"},
                "task_id": {"type": "string"},
                "origin": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_catalog_list",
        "description": "List deterministic Agent DevKit catalog items with optional filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "provider": {"type": "string"},
                "status": {"type": "string"},
                "write_policy": {"type": "string"},
                "readiness": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_catalog_search",
        "description": "Search agents, capabilities and providers in the deterministic Agent DevKit catalog.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "type": {"type": "string"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_catalog_show",
        "description": "Show one deterministic Agent DevKit catalog item.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string"},
            },
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_route_explain",
        "description": "Explain how Agent DevKit would route a prompt without executing it.",
        "inputSchema": {
            "type": "object",
            "properties": {"prompt": {"type": "string"}},
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_agent_prompt_dry_run",
        "description": "Build a dry-run agentic execution plan for a natural-language prompt.",
        "inputSchema": {
            "type": "object",
            "properties": {"prompt": {"type": "string"}},
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_agentic_plan",
        "description": "Build the explicit v0.2.1 agentic plan contract for a natural-language prompt.",
        "inputSchema": {
            "type": "object",
            "properties": {"prompt": {"type": "string"}},
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_eval_list",
        "description": "List deterministic Agent DevKit eval suites.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_eval_run",
        "description": "Run one deterministic Agent DevKit eval suite.",
        "inputSchema": {
            "type": "object",
            "properties": {"suite": {"type": "string"}},
            "required": ["suite"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_secrets_doctor",
        "description": "Diagnose secret reference backends without exposing values.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_workflow_list",
        "description": "List installable Agent DevKit workflows.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_workflow_show",
        "description": "Show one installable Agent DevKit workflow.",
        "inputSchema": {
            "type": "object",
            "properties": {"workflow_id": {"type": "string"}},
            "required": ["workflow_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_workflow_run_dry_run",
        "description": "Build a dry-run payload for an installable workflow.",
        "inputSchema": {
            "type": "object",
            "properties": {"workflow_id": {"type": "string"}},
            "required": ["workflow_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_llm_list",
        "description": "List local LLM operational workers.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_local_llm_doctor",
        "description": "Diagnose local LLM/Ollama readiness without installing models.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_local_llm_models",
        "description": "List local LLM models known to Ollama when available.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_local_artifacts_list",
        "description": "List local skills, scripts, automations and local agents stored in Agent DevKit home.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_local_skill_create",
        "description": "Create a local Agent DevKit skill artifact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "description": {"type": "string"},
                "force": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_skill_list",
        "description": "List local Agent DevKit skill artifacts.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_local_skill_show",
        "description": "Show one local Agent DevKit skill artifact.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_script_create",
        "description": "Create a local Agent DevKit shell script artifact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "command": {"type": "string"},
                "force": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_script_list",
        "description": "List local Agent DevKit shell script artifacts.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_local_script_run_dry_run",
        "description": "Plan execution of one local Agent DevKit script without running it.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_agent_create",
        "description": "Create a local Agent DevKit specialist agent scaffold.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "description": {"type": "string"},
                "force": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_agent_list",
        "description": "List local Agent DevKit specialist agent scaffolds.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_local_agent_show",
        "description": "Show one local Agent DevKit specialist agent scaffold.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_agent_validate",
        "description": "Validate one local Agent DevKit specialist agent scaffold.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_automation_create",
        "description": "Create a local Agent DevKit automation artifact in the user home.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "prompt": {"type": "string"},
                "command": {"type": "string"},
                "every": {"type": "string"},
                "cron": {"type": "string"},
                "force": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_automation_list",
        "description": "List local Agent DevKit automation artifacts.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_local_automation_show",
        "description": "Show one local Agent DevKit automation artifact.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_automation_enable",
        "description": "Enable one local Agent DevKit automation artifact.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_automation_disable",
        "description": "Disable one local Agent DevKit automation artifact.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_local_automation_validate",
        "description": "Validate one local Agent DevKit automation artifact.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_team_status",
        "description": "Inspect project-local team profile status without exposing secrets.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_team_doctor",
        "description": "Run project-local team profile diagnostics without exposing secrets.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_team_init",
        "description": "Create a project-local team profile file without storing secrets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "force": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_team_onboard",
        "description": "Return the project-local team onboarding checklist.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_team_profile_list",
        "description": "List profiles in the project-local team profile file.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_team_profile_show",
        "description": "Show one project-local team profile without exposing secrets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "profile_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_team_profile_export",
        "description": "Export one project-local team profile, or return a write plan when path is omitted.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "profile_id": {"type": "string"},
                "path": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_team_profile_import",
        "description": "Import a secret-free team profile into a project-local team profile file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_doctor",
        "description": "Run file-first knowledge base diagnostics for the current project.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_init",
        "description": "Initialize a file-first shared knowledge base in a project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "force": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_index",
        "description": "Rebuild the local lexical index for a file-first knowledge base.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_search",
        "description": "Search the local file-first knowledge base lexical index.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "query": {"type": "string"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_curate",
        "description": "Run local curation checks over a file-first knowledge base.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_sync",
        "description": "Return the current local-only knowledge sync status.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_snapshot_create",
        "description": "Create a sanitized pending knowledge snapshot in a file-first knowledge base.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "from_file": {"type": "string"},
                "type": {"type": "string"},
            },
            "required": ["title"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_snapshot_list",
        "description": "List pending, accepted and rejected knowledge snapshots.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_snapshot_show",
        "description": "Show one knowledge snapshot content and metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "snapshot_id": {"type": "string"},
            },
            "required": ["snapshot_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_snapshot_score",
        "description": "Score a pending knowledge snapshot for usefulness, safety and duplication.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "snapshot_id": {"type": "string"},
            },
            "required": ["snapshot_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_snapshot_submit",
        "description": "Submit a knowledge snapshot for owner review when it passes local score gates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "snapshot_id": {"type": "string"},
            },
            "required": ["snapshot_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_review_list",
        "description": "List knowledge snapshot reviews.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_review",
        "description": "Review one pending knowledge snapshot without publishing it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "snapshot_id": {"type": "string"},
            },
            "required": ["snapshot_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_publish",
        "description": "Publish an approved knowledge snapshot. Requires yes=true and the configured owner agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "snapshot_id": {"type": "string"},
                "yes": {"type": "boolean"},
                "owner_agent": {"type": "string"},
            },
            "required": ["snapshot_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_base_create",
        "description": "Create a file-first knowledge base in a project directory with a canonical knowledge provider.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "provider": {"type": "string"},
                "force": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_base_join",
        "description": "Create local config for joining an existing knowledge base id without remote sync.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "kb_id": {"type": "string"},
                "provider": {"type": "string"},
                "force": {"type": "boolean"},
            },
            "required": ["kb_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_base_status",
        "description": "Inspect file-first knowledge base status for a project directory.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_base_tokens",
        "description": "List knowledge base token references without returning token values.",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_knowledge_base_rotate_token",
        "description": "Rotate a knowledge base token reference fingerprint without exposing token values.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "scope": {"type": "string"},
            },
            "required": ["scope"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_roadmap",
        "description": "Return the deterministic Agent DevKit roadmap payload.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_source_list",
        "description": "List configured sources without exposing secrets.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "agent_devkit_source_status",
        "description": "Inspect source readiness without exposing secrets.",
        "inputSchema": {
            "type": "object",
            "properties": {"source_id": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_wizard_show",
        "description": "Show a pending setup wizard.",
        "inputSchema": {
            "type": "object",
            "properties": {"wizard_id": {"type": "string"}},
            "required": ["wizard_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "agent_devkit_wizard_answer",
        "description": "Answer a pending setup wizard question.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "wizard_id": {"type": "string"},
                "answer": {"type": "string"},
            },
            "required": ["wizard_id", "answer"],
            "additionalProperties": False,
        },
    },
]


def mcp_manifest() -> dict[str, Any]:
    return {
        "kind": "mcp-manifest",
        "status": "ok",
        "schema_version": "ai-devkit.mcp-manifest/v1",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "transport": "stdio",
        "server": {
            "name": MCP_SERVER_NAME,
            "version": __version__,
        },
        "tools": mcp_tools(),
        "host_config": {
            "mcpServers": {
                MCP_SERVER_NAME: {
                    "command": "agent",
                    "args": ["mcp", "serve"],
                }
            }
        },
    }


def mcp_tools_payload() -> dict[str, Any]:
    return {
        "kind": "mcp-tools",
        "status": "ok",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "transport": "stdio",
        "tools": mcp_tools(),
    }


def mcp_tools() -> list[dict[str, Any]]:
    return [dict(tool) for tool in TOOL_DEFINITIONS]


def mcp_doctor() -> dict[str, Any]:
    return {
        "kind": "mcp-doctor",
        "status": "ok",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "transport": "stdio",
        "server": {
            "name": MCP_SERVER_NAME,
            "version": __version__,
        },
        "tools": {
            "count": len(TOOL_DEFINITIONS),
            "names": [tool["name"] for tool in TOOL_DEFINITIONS],
        },
        "checks": {
            "stdio_transport": True,
            "json_rpc": True,
            "core_runtime": True,
            "secrets_redacted": True,
            "host_specific_dependency": False,
        },
    }
