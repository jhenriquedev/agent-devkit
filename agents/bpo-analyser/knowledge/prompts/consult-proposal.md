# Prompt: Consult BPO Proposal

## Objetivo

Consultar e resumir uma proposta BPO por numero, destacando status de
processamento, situacao, atividade, valores e observacoes.

## Entradas

- `--proposal-number` obrigatorio.
- `--format {markdown,json}`, `--fixture` e `--output` opcionais.

## Raciocinio

1. Valide que o numero da proposta nao esta vazio.
2. Chame `ServicoAPI.consultarPropostaPorNumeroProposta` via runner.
3. Leia `processing_status.status`, `situacao`, `atividade`,
   `motivoReprovacao`, valores e observacoes.
4. Mapeie a situacao pelo glossario BPO.

## Decisao

- `processing_status.status == false` e ponto de atencao: a BPO sinalizou falha
  de processamento. Reporte `error_message` se houver.
- `motivoReprovacao` preenchido e fato de reprovacao registrada.
- Situacao ausente deve ser reportada como ausencia; nao infira aprovacao.

## Saida

Seções de Fatos da proposta, Observacoes e Inferencias quando houver. Inclua
proposta, contrato, formalizacao, status, situacao, atividade, cliente, CPF mascarado, produto, tipo e valores.

## Nao faca

Nao chame alvos configurados em `BPO_FORBIDDEN_URL_PATTERNS`. Nao exiba CPF
completo, senha, token ou payload SOAP bruto. Nao conclua situacao final alem do
que a BPO retornou.
