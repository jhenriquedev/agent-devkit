# Classify Root Cause

## Objetivo

Classificar a causa raiz na taxonomia fixa N2.

## Entradas

- Contexto N2.
- Evidencias e gaps.
- Analise de codigo.
- Taxonomia `knowledge/runbooks/root-cause-taxonomy.md`.

## Raciocinio

1. Verifique se ha arquivos candidatos.
2. Procure sinais de erro backend, provider externo ou divergencia de dados.
3. Use gaps abertos como missing evidence.
4. Escolha uma categoria unica.
5. Atribua confianca honesta.
6. Gere resumo rastreavel.

## Rubrica/Regras

- `backend_bug`: erro/falha + codigo localizado.
- `data_inconsistency`: divergencia de banco/estado.
- `external_provider_issue`: BPO/provider sem sinal claro de bug.
- `insufficient_evidence`: sem evidencia suficiente.

## Saida

JSON com `category`, `confidence`, `summary`, `evidence`, `contradictions` e
`missingEvidence`.

## Nao faca

- Nao elevar confianca sem fonte.
- Nao marcar plano pronto com `insufficient_evidence`.
