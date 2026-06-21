# Workflow: Mover Card

## Objetivo

Alterar estado e, opcionalmente, coluna de um card com preview completo.

## Execucao local

```bash
./ai-devkit run azure-devops-orchestrator mover-card --project <project> --id <work-item-id> --state Active
```

Para executar a escrita real:

```bash
./ai-devkit run azure-devops-orchestrator mover-card --project <project> --id <work-item-id> --state Active --execute
```

## Passos

1. Validar projeto, ID e estado alvo.
2. Ler card atual.
3. Comparar estado/coluna atuais com alvo.
4. Classificar risco da movimentacao.
5. Mostrar operacoes planejadas.
6. Executar update apenas com `--execute`.

## Guardrails

- Nao mover para fechamento sem motivo.
- Nao executar update quando nao houver mudanca real.
- Nao inferir coluna alvo automaticamente.
