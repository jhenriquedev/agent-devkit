"""Objective acceptance criteria contract for Agent DevKit work."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


ACCEPTANCE_SECTIONS: list[dict[str, Any]] = [
    {
        "id": "contract",
        "name": "Contrato",
        "questions": [
            "Qual superficie publica sera criada, alterada ou preservada?",
            "Quais entradas, saidas, erros e limites ficam documentados?",
        ],
        "required": [
            "manifest_or_public_api",
            "inputs_outputs",
            "error_contract",
        ],
    },
    {
        "id": "behavior",
        "name": "Comportamento",
        "questions": [
            "Qual fluxo principal deve funcionar para o usuario ou agente chamador?",
            "Quais tarefas conhecidas devem ser deterministicamente automatizadas?",
        ],
        "required": [
            "happy_path",
            "known_failure_modes",
            "deterministic_scope",
        ],
    },
    {
        "id": "security",
        "name": "Seguranca",
        "questions": [
            "Quais permissoes, escritas externas ou dados sensiveis podem ser tocados?",
            "Quais guardrails impedem vazamento de segredo ou acao destrutiva?",
        ],
        "required": [
            "permission_policy",
            "secret_handling",
            "external_write_policy",
        ],
    },
    {
        "id": "compatibility",
        "name": "Compatibilidade",
        "questions": [
            "Quais comandos, aliases, manifests ou hosts existentes precisam continuar funcionando?",
            "A mudanca exige migracao ou aceita comportamento legado?",
        ],
        "required": [
            "backward_compatibility",
            "migration_notes",
            "host_compatibility",
        ],
    },
    {
        "id": "validation",
        "name": "Validacao",
        "questions": [
            "Quais testes ou comandos focados provam o comportamento novo?",
            "Quais validacoes manuais ou de CLI precisam ser executadas?",
        ],
        "required": [
            "focused_tests",
            "cli_smoke_test",
            "validation_evidence",
        ],
    },
    {
        "id": "out_of_scope",
        "name": "Fora de escopo",
        "questions": [
            "O que foi deliberadamente deixado para outro item?",
            "Quais riscos residuais permanecem aceitos temporariamente?",
        ],
        "required": [
            "deferred_items",
            "residual_risks",
        ],
    },
]


GLOBAL_ACCEPTANCE_CRITERIA: list[str] = [
    "A mudanca preserva o Agent DevKit como agente principal e trata agentes internos como modulos especialistas.",
    "A implementacao privilegia automacoes deterministicas para tarefas conhecidas e usa LLM apenas quando decisao, conversa ou revisao exigem raciocinio aberto.",
    "A instalacao continua simples, sem dependencia obrigatoria de host, LLM profissional ou servico externo especifico.",
    "Contratos publicos ficam versionados em codigo ou manifesto, nao apenas em docs locais ignorados pelo Git.",
    "Escritas externas, segredos e acoes destrutivas permanecem bloqueadas por padrao ou exigem permissao explicita.",
]


CHANGE_TYPE_ACCEPTANCE: dict[str, list[str]] = {
    "agent": [
        "Inclui agent.yaml valido, README, AGENTS.md e ownership claro do dominio.",
        "Define capabilities publicas sem depender de contexto grande carregado por padrao.",
        "Explicita quando usa runner deterministico, LLM externo, mini brain local ou intervencao humana.",
    ],
    "capability": [
        "Inclui capability.yaml com entrada, saida, write_policy e runner quando executavel.",
        "Mantem conhecimento detalhado sob demanda em knowledge/ ou templates/ da propria capability.",
        "Tem validacao focada que exercita o caminho principal via agent run quando aplicavel.",
    ],
    "runner": [
        "Recebe argumentos estruturados e retorna resultado estruturado ou erro explicito.",
        "Evita parse textual fragil quando houver API, JSON, YAML ou biblioteca adequada.",
        "Redige stdout, stderr e artefatos antes de persistir dados que possam conter segredos.",
    ],
    "integration": [
        "Fica encapsulada em infra/integrations/<provider>/ ou camada global equivalente quando o provider for compartilhado.",
        "Separa dry-run, leitura, escrita local e escrita externa.",
        "Documenta autenticacao, variaveis de ambiente e modo offline quando existir.",
    ],
    "host_plugin": [
        "Mantem adaptador fino para o host e delega logica de produto ao runtime do Agent DevKit.",
        "Preserva compatibilidade com CLI e MCP quando a funcao tambem fizer sentido fora do host.",
        "Nao torna Codex, Claude, OpenClaw, OpenCode ou outro host dependencia obrigatoria da instalacao base.",
    ],
    "core_change": [
        "Atualiza contratos publicos, validadores e saida humana quando a semantica do runtime mudar.",
        "Mantem compatibilidade de comandos publicos ou documenta migracao objetiva.",
        "Inclui testes focados cobrindo a nova regra central e pelo menos um smoke test de CLI quando aplicavel.",
    ],
}


DEFINITION_OF_DONE: list[str] = [
    "Contrato, comportamento, seguranca, compatibilidade, validacao e fora de escopo foram avaliados.",
    "A mudanca tem teste ou comando focado que prova o comportamento principal.",
    "A saida publica continua compreensivel para humano e consumivel por automacao quando houver modo JSON.",
    "Nenhum segredo, path local sensivel ou dependencia externa obrigatoria foi introduzido sem contrato.",
    "Riscos residuais e itens adiados ficaram explicitos na spec, PR ou resposta de entrega.",
]


def acceptance_sections() -> list[str]:
    """Return canonical acceptance section identifiers."""
    return [section["id"] for section in ACCEPTANCE_SECTIONS]


def change_type_acceptance() -> dict[str, list[str]]:
    """Return acceptance criteria grouped by change type."""
    return deepcopy(CHANGE_TYPE_ACCEPTANCE)


def acceptance_model() -> dict[str, Any]:
    """Return the canonical acceptance model exposed by public architecture output."""
    return {
        "schema_version": "ai-devkit.acceptance/v1",
        "sections": deepcopy(ACCEPTANCE_SECTIONS),
        "global_criteria": list(GLOBAL_ACCEPTANCE_CRITERIA),
        "change_types": [
            {
                "id": change_type,
                "criteria": list(criteria),
            }
            for change_type, criteria in CHANGE_TYPE_ACCEPTANCE.items()
        ],
        "definition_of_done": list(DEFINITION_OF_DONE),
    }
