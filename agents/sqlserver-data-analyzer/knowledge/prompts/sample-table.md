# Prompt: sample-table

## OBJETIVO
Obter uma amostra TOP N de linhas de uma tabela com mascaramento automático
de colunas sensíveis.

## ENTRADAS
- `schema` (obrigatório).
- `table` (obrigatório).
- `limit` (opcional, default 20): tamanho da amostra.

## RACIOCÍNIO (passos)
1. Se faltar `schema` ou `table`, peça ao usuário antes de executar.
2. Execute a capability `sample-table --schema <s> --table <t> --limit <n>`.
3. O runner aplica mascaramento via `mask_if_sensitive` antes de renderizar.
4. Leia `row_count` e `rows[]`.
5. Se colunas sensíveis aparecerem, confirme que estão mascaradas.

## RUBRICA / REGRAS DE DECISÃO
- Prefira amostra pequena (default 20) para inspeção; aumente só se necessário.
- Se a tabela for grande, use `estimate-table-size` antes para calibrar o limite.
- Se todas as colunas importantes aparecerem mascaradas, sugira `profile-table`
  para estatísticas sem exposição de dados.

## SAÍDA
`row_count` + tabela mascarada. Nota explícita se alguma coluna foi mascarada.

## NÃO FAÇA
- Não use esta capability para "extrair" base de dados pessoais.
- Não aumente o limite para além do necessário para inspeção estrutural.
- Não exiba CPF, CNPJ, email, telefone, nome, endereço, token ou senha brutos.
