# Prompt: trace-record

## OBJETIVO
Rastrear um registro específico e seus relacionamentos via FKs, com
mascaramento de dados pessoais.

## ENTRADAS
- `schema` (obrigatório).
- `table` (obrigatório).
- `key-column` (obrigatório): coluna de chave (ex.: `id`).
- `key-value` (obrigatório): valor da chave a rastrear.

## RACIOCÍNIO (passos)
1. Se faltar algum dos quatro parâmetros, peça ao usuário.
2. Execute a capability `trace-record`.
3. Leia `base_rows[]` (mascaradas pelo runner) e `relationships[]` — FKs do
   schema que referenciam esta tabela.
4. Indique quais tabelas relacionadas podem conter dados do registro.

## RUBRICA / REGRAS DE DECISÃO
- `base_rows` vazio → registro não encontrado; confirme chave com o usuário.
- Apresente caminhos de relacionamento (não despeje tabelas filhas inteiras).
- Dados pessoais em `base_rows` devem estar mascarados pelo runner; se não
  estiverem, não os exiba e reporte.

## SAÍDA
Linha base (mascarada) + lista de tabelas relacionadas via FK com orientação
de navegação.

## NÃO FAÇA
- Não despeje tabelas filhas inteiras — apenas indique os caminhos.
- Não exiba dados pessoais brutos mesmo que o runner não os mascare.
- Não use `key-value` para injeção SQL (o runner usa `sql_literal`).
