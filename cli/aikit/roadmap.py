"""Incremental implementation phases for Agent DevKit evolution."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


RECOMMENDED_INITIAL_ORDER = [1, 2, 3, 4, 7, 8, 6, 5, 36]

IMPLEMENTATION_PHASES: list[dict[str, Any]] = [
    {
        "id": "phase-0",
        "number": 0,
        "name": "Decisao Arquitetural",
        "goal": "Confirmar o Agent DevKit como agente principal e estabilizar vocabulario arquitetural.",
        "principles": ["contrato antes de expansao"],
        "problems": [1],
        "deliverables": [
            "Decisao clara de que Agent DevKit e o agente principal.",
            "Vocabulario canonico para core, modulo especialista, capability, runner, provider, host e LLM.",
        ],
        "exit_conditions": [
            "Specs seguintes usam o vocabulario canonico sem contradicao.",
        ],
    },
    {
        "id": "phase-1",
        "number": 1,
        "name": "Fundacao Do Core",
        "goal": "Separar nucleo reutilizavel da CLI e estabilizar contratos centrais de execucao.",
        "principles": ["core antes de novas interfaces", "contrato antes de expansao"],
        "problems": [2, 3, 4, 6],
        "deliverables": [
            "Core chamavel sem argparse.",
            "Contratos canonicos de request e result.",
            "Policy efetiva unica.",
            "Registry carregando metadata declarativa.",
        ],
        "exit_conditions": [
            "CLI segue funcionando sobre o core.",
            "Core pode ser usado por futura interface MCP.",
            "Execution plan evita hardcodes para casos novos.",
        ],
    },
    {
        "id": "phase-2",
        "number": 2,
        "name": "Seguranca E Observabilidade",
        "goal": "Garantir comportamento auditavel, previsivel e seguro antes de aumentar autonomia.",
        "principles": ["seguranca antes de autonomia"],
        "problems": [7, 8, 9, 11, 12],
        "deliverables": [
            "Sources nao persistem segredos.",
            "Auditoria falha de forma observavel.",
            "Gates distinguem contrato funcional e release.",
            "Criterios de aceite e mapa de impacto ficam explicitos.",
        ],
        "exit_conditions": [
            "Execucoes read-only, output local e writes confirmadas tem comportamento auditavel e previsivel.",
        ],
    },
    {
        "id": "phase-3",
        "number": 3,
        "name": "Planner E Execucao Multiagente",
        "goal": "Evoluir roteamento e planejamento para tarefas compostas com trace e revisao.",
        "principles": ["automacao deterministica antes de LLM"],
        "problems": [5, 30, 31, 32, 33],
        "deliverables": [
            "Planner explicavel.",
            "Baixa confianca com pergunta ao usuario.",
            "Handoff, revisao e criterio de parada entre modulos.",
            "Politica de escolha entre automacao, LLM e humano.",
        ],
        "exit_conditions": [
            "Agent DevKit planeja e executa tarefas compostas com trace e revisao.",
        ],
    },
    {
        "id": "phase-4",
        "number": 4,
        "name": "MCP E Multi-Host",
        "goal": "Expor o core para hosts externos por MCP e adaptadores opcionais.",
        "principles": ["integracao opcional antes de dependencia"],
        "problems": [23, 36],
        "deliverables": [
            "agent mcp serve.",
            "Tools MCP para agents, capabilities, doctor, source e wizard.",
            "Configs opcionais de host.",
        ],
        "exit_conditions": [
            "Hosts externos usam Agent DevKit sem dependencia obrigatoria no setup base.",
        ],
    },
    {
        "id": "phase-5",
        "number": 5,
        "name": "Agentes Criadores E Geradores",
        "goal": "Criar agentes que geram artefatos seguindo contratos e gates do projeto.",
        "principles": ["contrato antes de expansao", "automacao deterministica antes de LLM"],
        "problems": [13, 14, 15, 18, 20, 21, 22],
        "deliverables": [
            "Geradores de agentes, automacoes, Lambda, Docker e loops.",
            "Dry-run de geracao.",
            "Templates canonicos e quality gates automaticos.",
        ],
        "exit_conditions": [
            "Um agente criador gera capability ou agente valido sem quebrar o validator.",
        ],
    },
    {
        "id": "phase-6",
        "number": 6,
        "name": "Ferramentas De Automacao",
        "goal": "Padronizar automacao de browser, UI e scripts com guardrails.",
        "principles": ["seguranca antes de autonomia"],
        "problems": [16, 17, 27],
        "deliverables": [
            "Matriz Playwright, Selenium e PyAutoGUI.",
            "Guardrails para automacao visual.",
            "Templates e runners seguros.",
        ],
        "exit_conditions": [
            "Automacoes geradas sao auditaveis, idempotentes quando possivel e bloqueiam acoes perigosas.",
        ],
    },
    {
        "id": "phase-7",
        "number": 7,
        "name": "Integracoes Operacionais E Notificacoes",
        "goal": "Adicionar canais opcionais de notificacao e comunicacao operacional.",
        "principles": ["integracao opcional antes de dependencia"],
        "problems": [24, 25, 26, 28, 29],
        "deliverables": [
            "Notificacoes locais e remotas.",
            "Canais opcionais.",
            "Auditoria por canal.",
        ],
        "exit_conditions": [
            "Nenhuma integracao de mensagem e dependencia obrigatoria do setup base.",
        ],
    },
    {
        "id": "phase-8",
        "number": 8,
        "name": "Dominios Especializados",
        "goal": "Adicionar dominios especialistas apos estabilizar core, seguranca e interfaces.",
        "principles": ["contrato antes de expansao"],
        "problems": [19],
        "deliverables": [
            "Agente Supabase para schema, RLS, migrations, Edge Functions, performance e seguranca.",
        ],
        "exit_conditions": [
            "O dominio especializado segue contrato de agente, capability e provider.",
        ],
    },
    {
        "id": "phase-9",
        "number": 9,
        "name": "Mini Cerebro Local E Autonomia",
        "goal": "Introduzir mini cerebro local e autonomia gradual sem assumir decisoes de alto risco.",
        "principles": ["seguranca antes de autonomia", "integracao opcional antes de dependencia"],
        "problems": [34, 35],
        "deliverables": [
            "Mini cerebro local para setup, wizard e conversa simples.",
            "Politica de uso de LLM local, externa e humano.",
            "Autonomia gradual para tarefas conhecidas.",
        ],
        "exit_conditions": [
            "Mini cerebro nao assume decisoes de alto risco.",
            "Tarefas complexas continuam podendo usar LLM forte.",
        ],
    },
]


def implementation_phases() -> list[dict[str, Any]]:
    return deepcopy(IMPLEMENTATION_PHASES)


def recommended_initial_order() -> list[int]:
    return list(RECOMMENDED_INITIAL_ORDER)


def problem_phase_map() -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for phase in IMPLEMENTATION_PHASES:
        for problem in phase["problems"]:
            result[int(problem)] = {
                "phase_id": phase["id"],
                "phase_number": phase["number"],
                "phase_name": phase["name"],
            }
    return result
