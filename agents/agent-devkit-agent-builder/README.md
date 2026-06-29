# Agent DevKit Agent Builder

Agente especialista interno para planejar, criar scaffold e validar novos
agentes do Agent DevKit.

## Capabilities

- `plan-agent`: analisa uma spec estruturada e retorna o plano de agente sem
  escrever arquivos.
- `scaffold-agent`: gera o scaffold do agente em dry-run por padrao e escreve
  arquivos somente com execucao confirmada.
- `validate-agent-contract`: valida a estrutura de um agente gerado.

## Exemplo

```bash
agent run agent-devkit-agent-builder plan-agent --spec docs/new-agent.yaml
agent run agent-devkit-agent-builder scaffold-agent --spec docs/new-agent.yaml
agent run agent-devkit-agent-builder scaffold-agent --spec docs/new-agent.yaml --execute --confirm-execute
agent run agent-devkit-agent-builder validate-agent-contract --agent-id sample-agent
```

## Spec Minima

```yaml
agent_id: sample-agent
name: Sample Agent
purpose: >
  Descrever o objetivo do agente.
domain: dominio interno
capabilities:
  - id: do-thing
    purpose: Executar uma tarefa controlada.
    write_policy: read_only
providers: []
risk_profile: low
```
