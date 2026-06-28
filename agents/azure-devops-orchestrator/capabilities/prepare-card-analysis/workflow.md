# Workflow: Preparar Analise Card

## Objetivo

Transformar um card em uma analise operacional para sustentacao, sem executar
escrita no Azure DevOps.

## Execucao local

```bash
agent run azure-devops-orchestrator prepare-card-analysis --project <project> --id <work-item-id> --include-comment-draft
```

## Passos

1. Validar projeto e ID.
2. Ler card com comentarios e anexos.
3. Classificar demanda.
4. Separar fatos, hipoteses e lacunas.
5. Sugerir proximos passos.
6. Opcionalmente gerar comentario sugerido.

## Guardrails

- Nao escrever no Azure.
- Nao afirmar causa raiz sem evidencia.
- Indicar lacunas e incertezas.
