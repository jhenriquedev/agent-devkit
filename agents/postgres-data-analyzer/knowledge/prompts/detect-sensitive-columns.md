# Prompt: detect-sensitive-columns

> Operação read-only. Resultados são INFERÊNCIA por nome de coluna. Separe dados de inferências.

## Objetivo
Listar colunas potencialmente sensíveis (PII/segredos) usando heurística de nome de coluna
(sensitive_kind), como preparação para mascaramento antes de exibir dados.

## Entradas esperadas
- `schema` (opcional): restringir ao schema.
- `database` (opcional).

## Passos de raciocínio
1. Execute `detect-sensitive-columns`.
2. Agrupe resultados por `sensitive_kind` (cpf, cnpj, email, phone, name, address,
   password, token).
3. Exiba em tabela com schema.table.column e kind.
4. **Declare explicitamente**: detecção é por nome de coluna, NÃO por conteúdo —
   pode haver falso positivo e falso negativo.

## Regras de decisão
- Tratar resultado como ponto de partida para mascaramento — não como classificação definitiva.
- Coluna com `password` ou `token` no nome → mascarar/omitir em qualquer exibição de linha.
- Recomende confirmar com regra de negócio antes de classificar como PII definitiva.

## Saída
Tabela: `table_schema`, `table_name`, `column_name`, `data_type`, `sensitive_kind`.
Nota ao final: "⚠ INFERÊNCIA: classificação baseada em heurística de nome de coluna."

## NÃO faça
- Não afirme que uma coluna contém PII como fato baseado só no nome.
- Não exiba amostras de valores das colunas sensíveis.
