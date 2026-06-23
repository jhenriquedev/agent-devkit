# Prompt: generate-data-report

> Operação read-only. PII mascarada. Separe SEMPRE dados coletados de inferências/recomendações.

## Objetivo
Gerar relatório Markdown completo de uma tabela combinando perfil de colunas, detecção
de sensibilidade e recomendações, para uso em auditorias e governança de dados.

## Entradas esperadas
- `schema` (obrigatório).
- `table` (obrigatório).
- `limit_columns` (default 30).
- `database` (opcional).

## Passos de raciocínio
1. Execute `generate-data-report` (compõe `profile-table` + `detect-sensitive-columns`).
2. Organize o relatório nas 5 seções abaixo.
3. Marque `null_ratio > 0.5` como "alto null" (threshold de `policies.data_quality_thresholds`).
4. Recomendações são INFERÊNCIA — rotule explicitamente.

## Regras de decisão
- `null_ratio > 0.5` = "alto null" → investigar antes de usar em análise.
- Colunas sensíveis → recomendar revisão de acesso antes de compartilhar.
- Não inclua amostras de linhas — apenas métricas agregadas.
- PII mascarada em todas as saídas.

## Saída (5 seções obrigatórias)
```markdown
# Postgres Data Report — schema.table

## Escopo
- Database: <db> | Schema: <schema> | Tabela: <table> | Total de linhas: N

## Dados coletados

### Colunas Sensíveis (INFERÊNCIA por nome)
Tabela: column_name, sensitive_kind.

### Colunas com Alto Null (null_ratio > 0.5)
Tabela: column_name, null_ratio.

### Perfil de Colunas
Tabela: column_name, data_type, total_rows, null_count, distinct_count.

## Inferências e Recomendações
- Revisar colunas sensíveis antes de compartilhar resultados.
- Investigar colunas com alto null antes de usar em análises.
- (outras recomendações específicas da tabela)
```

## NÃO faça
- Não inclua amostras de linhas.
- Não exponha CPF, token ou senha.
- Não misture dados coletados com inferências sem rotulação.
