# Context

Agentes genericos podem ser consumidos por hosts diferentes:

- Codex e OpenCode: normalmente usam `AGENTS.md`.
- Claude: pode usar `CLAUDE.md`, skills ou subagents, conforme o ambiente.
- Cursor: pode usar regras em `.cursor/rules/*.mdc`.
- Generic: usa instrucoes Markdown portaveis sem assumir host especifico.

O agente gerado deve conter apenas capacidades suportadas pelo host e pelas
ferramentas declaradas no contrato de entrada.
