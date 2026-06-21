# Decision Rules: Gerar Relatorio Cards

- A capability e sempre read-only.
- Use `--project` para Azure real; `AZURE_DEVOPS_PROJECT` e apenas fallback da infra.
- Quando `--include-comments` for usado, carregue comentarios de cada card.
- Considere card sem responsavel quando `assigned_to` estiver vazio.
- Considere card sem criterios quando `acceptance_criteria` estiver vazio.
- Conte anexos por relations com `rel == AttachedFile`.
- Se o numero de cards retornados for igual ao limite, sinalize possivel truncamento da consulta.
