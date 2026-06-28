# Decision Rules

- Correlacionar evidencias runtime com achados de codigo sem escrever `patch_plan.md`.
- Separar evidencia confirmatoria, contradicao e evidencia ausente.
- Usar logs, checks N1, BPO, banco e card como fontes rastreaveis.
- Nao tratar ausencia de log como ausencia de erro quando a fonte ou janela estiver incompleta.
- Relacionar request id, correlation id, proposta e timestamps aos arquivos candidatos quando possivel.
- Preservar lacunas vindas do N1 e adicionar lacunas N2 quando a correlacao for insuficiente.
- Nao alterar a decisao final nesta capability; apenas informar a classificacao posterior.
- Reduzir amostras de log ao minimo necessario e mascarar PII.
- Registrar divergencias entre runtime e codigo para evitar patch no arquivo errado.
- A saida deve alimentar `classify-root-cause` e `review-patch-plan-readiness`.
