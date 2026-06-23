# Prompt: suggest-joins

> Operação read-only. Marque heurísticas como INFERÊNCIA. Separe dados de inferências.

## Objetivo
Sugerir possíveis joins entre tabelas usando heurística de nome de coluna (sem FK real),
para orientar construção de queries de análise.

## Entradas esperadas
- `schema` (opcional): restringir sugestões ao schema.
- `database` (opcional).

## Passos de raciocínio
1. Execute `suggest-joins`.
2. Leia `suggestions` com `left_table`, `left_column`, `right_table`, `right_column`,
   `confidence`.
3. Apresente as sugestões em tabela.
4. **Marque cada sugestão como INFERÊNCIA (heurística por nome de coluna)**, especialmente
   quando `confidence != "high"`.

## Regras de decisão
- Sugestões desta capability são **heurísticas** — não há FK confirmada.
- `confidence: high` = match exato de nome; `medium` = match parcial — ambas são inferência.
- Se 0 sugestões, informe e recomende `list-relationships` para FKs reais.

## Saída
Tabela markdown: `left_table`, `left_column`, `right_table`, `right_column`, `confidence`
+ nota "⚠ INFERÊNCIA: sugestões baseadas em heurística de nome de coluna, sem FK confirmada".

## NÃO faça
- Não apresente sugestões heurísticas como relacionamentos confirmados.
- Não leia dados de linha.
