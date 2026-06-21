# Workflow: Atribuir Card

## Objetivo

Atribuir um card a uma identidade resolvida no Azure DevOps, evitando escolha
automatica quando houver ambiguidade.

## Execucao local

```bash
./ai-devkit run azure-devops-orchestrator assign-card --project <project> --id <work-item-id> --assignee pessoa@example.com
```

Para executar a escrita real:

```bash
./ai-devkit run azure-devops-orchestrator assign-card --project <project> --id <work-item-id> --assignee pessoa@example.com --execute
```

## Passos

1. Validar projeto, ID e assignee.
2. Ler card atual.
3. Buscar identidade.
4. Bloquear se houver ambiguidade.
5. Mostrar responsavel atual e responsavel alvo.
6. Executar update apenas com `--execute`.

## Guardrails

- Preferir email ou unique name.
- Nao escolher automaticamente entre multiplos candidatos ambiguos.
- Nao executar update quando o responsavel alvo ja for o atual.
