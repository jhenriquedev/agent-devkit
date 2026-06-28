# Prompt: Analyze BPO CPF Proposals

## Objetivo

Analisar todas as propostas de um CPF, separando elegiveis, em analise e
reprovadas, e apontando a proposta mais recente integrada/aprovada.

## Entradas

- `--cpf` obrigatorio.
- `--format`, `--fixture` e `--output` opcionais.

## Raciocinio

1. Liste as propostas do CPF.
2. Classifique por `situation_kind`.
3. Elegiveis seguem a politica operacional configurada:
   `BPO_ELIGIBLE_SITUATIONS`, `BPO_ELIGIBLE_PROPOSAL_TYPES` e
   `BPO_REQUIRE_POSITIVE_WITHDRAW_LIMIT`.
4. Em analise inclui `cadastrada`, `pendente` e `andamento`.
5. Reprovadas usam `reprovada`.
6. Selecione a mais recente integrada/aprovada por `last_due_date`.

## Decisao

- Existe proposta em analise: ponto de atencao.
- Existe proposta reprovada: ponto de atencao e motivo deve ser checado por
  numero de proposta.
- Existe elegivel: sinalize, mas nao conclua contratacao.
- `has_blocking_signals` deriva de propostas em analise ou reprovadas.

## Saida

Resumo com CPF mascarado, total, elegiveis, em analise e reprovadas; proposta
mais recente; tabela completa; inferencias e pontos de atencao.

## Nao faca

Nao exiba CPF completo. Nao conclua aprovacao final. Nao chame alvos
configurados em `BPO_FORBIDDEN_URL_PATTERNS`. Nao relaxe a politica operacional.
