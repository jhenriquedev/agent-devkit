# Prompt: Consult BPO Attached Documents

## Objetivo

Listar documentos anexados a uma proposta BPO usando metadados: nome, tipo,
extensao, tamanho e presenca de conteudo.

## Entradas

- `--proposal-number` obrigatorio.
- `--document-type` opcional; default vem de `BPO_DEFAULT_DOCUMENT_TYPE`.
- `--include-content` opcional; traz ArquivoBase64/file_base64 e so deve ser
  usado por pedido explicito.

## Raciocinio

1. Valide proposta e tipo de documento.
2. Chame `WsProposta.ConsultaDocumentosAnexados` via runner.
3. Para cada arquivo, leia nome, tipo, extensao, tamanho, `has_file` e
   `has_file_base64`.
4. Trate conteudo binario como presenca, nao como texto interpretavel.

## Decisao

- Nenhum arquivo retornado e ponto de atencao factual.
- Sem `--include-content`, reporte apenas presenca de base64.
- Mesmo com `--include-content`, nao interprete o conteudo e nao duplique base64
  na resposta humana.

## Saida

Cabecalho com proposta, tipo solicitado, status de processamento e total, seguido
de tabela de documentos. Indique que a capability trata metadados e presenca.

## Nao faca

Nao imprima ArquivoBase64/file_base64. Nao interprete o conteudo do documento.
Nao afirme o que esta dentro do arquivo. Nao chame alvos configurados em
`BPO_FORBIDDEN_URL_PATTERNS`.
