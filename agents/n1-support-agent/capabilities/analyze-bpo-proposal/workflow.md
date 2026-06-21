# Analyze BPO Proposal

## Objetivo

Normalizar evidencias da BPO para o contrato do N1, sem acessar diretamente os
servicos BPO. A capability deve orquestrar o agente `bpo-analyser`.

## Fluxo

1. Receber numero de proposta ou CPF.
2. Quando houver proposta, executar `bpo-analyser/analyze-proposal`.
3. Quando houver apenas CPF, executar `bpo-analyser/analyze-cpf-proposals`.
4. Classificar o status operacional como `found`, `not_found`, `pending`,
   `rejected`, `unavailable` ou `skipped`.
5. Retornar fatos resumidos, pontos de atencao e metadados mascarados.

## Guardrails

- Nao chamar endpoints BPO diretamente.
- Nao imprimir CPF cru nem conteudo base64 de documentos.
- Falha da BPO nao deve interromper o runbook N1; retornar `unavailable`.
