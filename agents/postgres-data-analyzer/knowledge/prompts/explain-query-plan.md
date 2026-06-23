# Prompt: explain-query-plan

> Operação read-only. Separe dados coletados de inferências.

## Objetivo
Obter e interpretar o plano de execução de uma query (EXPLAIN) para identificar
gargalos de performance (seq scan em tabela grande, custo alto) sem executar a query real.

## Entradas esperadas
- `query` (obrigatório): query a analisar.
- `database` (opcional).

## Passos de raciocínio
1. Execute `explain-query-plan` (usa EXPLAIN sem ANALYZE — sem tocar nos dados).
2. Leia o `plan` retornado.
3. Interprete:
   - `Seq Scan` em tabela grande → potencial gargalo (INFERÊNCIA).
   - `Index Scan` / `Index Only Scan` → eficiente (fato do plano).
   - `cost=X..Y` alto → pode ser lento (INFERÊNCIA sem ANALYZE).
   - `rows=N` → estimativa do planner, não contagem real.
4. Aponte nós de alto custo e recomende índices se pertinente (INFERÊNCIA).

## Regras de decisão
- EXPLAIN sem ANALYZE: custo e rows são **estimativas do planner** — rotule como
  INFERÊNCIA.
- Não execute EXPLAIN ANALYZE (ativa a query real).

## Saída
```
# Postgres Query Plan
- Database: <db>
```
Bloco de texto do plano + seção **Análise** com observações rotuladas (fato vs inferência).

## NÃO faça
- Não execute EXPLAIN ANALYZE.
- Não afirme que a query "vai ser lenta" como fato — é estimativa.
