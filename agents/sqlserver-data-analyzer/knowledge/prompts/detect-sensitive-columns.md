# Prompt: detect-sensitive-columns

## OBJETIVO
Identificar colunas que, pelo nome, indicam conter dados pessoais sensíveis
(CPF, CNPJ, email, telefone, nome, endereço, senha, token).

## ENTRADAS
- `schema` (opcional): restringir ao schema.

## RACIOCÍNIO (passos)
1. Execute a capability `detect-sensitive-columns`.
2. Leia `columns[]` (campos: `table_schema`, `table_name`, `column_name`,
   `sensitive_kind`).
3. Agrupe por `sensitive_kind`; destaque tabelas com mais colunas sensíveis.

## RUBRICA / REGRAS DE DECISÃO
- Classificação é **inferência por padrão de nome** — pode ter falso positivo
  (ex.: `customer_name_prefix`) e falso negativo (ex.: coluna CPF nomeada
  `campo1`).
- Sempre marque como inferência; recomende confirmação por amostra mascarada
  (`sample-table`) ou análise direta (`analyze-cpf-column`).

## SAÍDA
Tabela com `table_schema`, `table_name`, `column_name`, `sensitive_kind` +
nota de inferência por nome.

## NÃO FAÇA
- Não apresente o resultado como lista oficial de campos LGPD sem validação.
- Não exiba valores dessas colunas.
