# Infra

Infraestrutura especializada do Azure DevOps Orchestrator.

## Objetivo

Guardar os recursos executaveis que conectam o agente a sistemas externos.

## Estrutura

```text
infra/
└─ integrations/
```

- `integrations/`: repositories, CLIs, models e contratos de metodos.

## Regras

- Acesso externo deve ser exposto por repositories conectaveis.
- Contratos reutilizaveis de API ficam em `integrations/<provider>/methods/`.
- Nao coloque conhecimento de decisao aqui; use `knowledge/`.
