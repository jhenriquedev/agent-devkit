# Prompt: Analyze BPO Proposal

## Objetivo

Consolidar a leitura operacional de uma proposta: dados essenciais, situacao,
status de processamento, observacoes, documentos anexados e inferencias separadas
dos fatos.

## Entradas

- `--proposal-number` obrigatorio.
- `--document-type`, `--format`, `--fixture` e `--output` opcionais.

## Raciocinio

1. Consulte a proposta no `ServicoAPI`.
2. Consulte anexos no `WsProposta`.
3. Compile fatos: situacao, atividade, `processing_status`, numero de
   observacoes, numero e tipos de documento.
4. Leia `inferences.attention_points` e `has_blocking_signals`.

## Decisao

- `has_blocking_signals == true` indica sinal que merece verificacao humana.
- Falha de processamento, situacao ausente, motivo de reprovacao, ausencia de
  observacoes e sem documentos devem aparecer como pontos de atencao.
- Proposta integrada ou aprovada sem documentos permite inferencia de possivel pendencia de formalizacao, nunca fato final.

## Saida

Resumo, Fatos da Proposta, Observacoes, Documentos e Inferencias/Pontos de
atencao. CPF sempre mascarado; sem base64 ou SOAP bruto.

## Nao faca

Nao sugira mutacao de esteira, formalizacao ou status. Nao use API SelfHire. Nao
trate inferencia como decisao final.
