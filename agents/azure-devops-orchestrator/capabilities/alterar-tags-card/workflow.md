# Workflow: Alterar Tags Card

## Objetivo

Adicionar ou remover tags de um card preservando tags existentes e exibindo o
diff antes da escrita.

## Execucao local

```bash
./ai-devkit run azure-devops-orchestrator alterar-tags-card --project <project> --id <work-item-id> --add-tag Bugfix
```

Para executar a escrita real:

```bash
./ai-devkit run azure-devops-orchestrator alterar-tags-card --project <project> --id <work-item-id> --add-tag Bugfix --execute
```

## Passos

1. Validar projeto, ID e tags de entrada.
2. Ler o card atual.
3. Normalizar tags atuais, tags a adicionar e tags a remover.
4. Calcular tags finais.
5. Mostrar diff e operacao planejada.
6. Executar `update-work-item` apenas com `--execute`.

## Guardrails

- Nao remover tags sem listá-las explicitamente.
- Nao duplicar tags por diferenca de casing.
- Nao executar update quando nao houver mudanca real.
