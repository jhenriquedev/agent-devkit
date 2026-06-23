# Prompt: detect-data-quality-issues

> Operação read-only. Não invente issues além das calculadas. Separe dados de inferências.

## Objetivo
Detectar problemas estruturais de qualidade de dados (colunas totalmente nulas ou com
valor constante) usando perfil agregado, sem expor valores individuais.

## Entradas esperadas
- `schema` (obrigatório).
- `table` (obrigatório).
- `database` (opcional).

## Passos de raciocínio
1. Execute `detect-data-quality-issues` (usa `profile_table` internamente).
2. Leia `issues` com `column_name` e `issue` (all_null / constant_value).
3. Para cada issue, descreva o impacto (INFERÊNCIA):
   - `all_null` → coluna sem dados; inútil para análise; considerar remoção.
   - `constant_value` → sem poder discriminativo; possível campo de auditoria ou flag fixo.
4. Se 0 issues, declare "Nenhuma issue de qualidade detectada neste escopo."

## Regras de decisão
- Só reporte issues calculadas pelo runner (all_null, constant_value).
- Não invente issues de outlier, formato incorreto, etc. — fora do escopo atual.
- Impactos são INFERÊNCIA — depende do contexto de negócio.

## Saída
Tabela: `column_name`, `issue`, `impacto (INFERÊNCIA)`.
Se vazio: "Nenhuma issue de qualidade detectada."

## NÃO faça
- Não invente issues não calculadas (outliers, duplicatas, etc.).
- Não exiba valores individuais das colunas.
