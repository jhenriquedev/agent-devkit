# Prompt: List BPO Proposals By CPF

## Objetivo

Listar todas as propostas vinculadas a um CPF, com situacao, tipo,
elegibilidade, limites e datas.

## Entradas

- `--cpf` obrigatorio, com 11 digitos apos normalizacao.
- `--format`, `--fixture` e `--output` opcionais.

## Raciocinio

1. Normalize o CPF removendo pontuacao e validando 11 digitos.
2. Chame `ServicoAPI.listarPropostasPorCpf` via runner.
3. Para cada proposta, exponha situacao, `situation_kind`, tipo, `is_eligible`,
   datas e valores.

## Decisao

- Lista vazia e fato: nenhuma proposta retornada para o CPF.
- `is_eligible` vem da politica operacional configurada; nao amplie a
  elegibilidade por inferencia.
- Esta capability lista; analise operacional em profundidade fica em
  `analyze-cpf-proposals`.

## Saida

Cabecalho com CPF mascarado e total, seguido de tabela de propostas com numero,
situacao, tipo, elegivel, ultimo vencimento, limite saque, valor liberado e
orgao.

## Nao faca

Nao exiba CPF completo. Nao imprima payload SOAP bruto. Nao chame alvos
configurados em `BPO_FORBIDDEN_URL_PATTERNS`. Nao conclua aprovacao final.
