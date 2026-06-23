# Prompt: explain-query-plan

## OBJETIVO
Obter o plano estimado de execução de uma query (`SET SHOWPLAN_TEXT ON`) sem
executá-la de fato.

## ENTRADAS
- `query` (obrigatório): SQL SELECT ou WITH.

## RACIOCÍNIO (passos)
1. Execute a capability `explain-query-plan --query "<sql>"`.
2. O runner executa cada statement em batch isolado: primeiro
   `SET SHOWPLAN_TEXT ON`, depois a query (sem retornar dados), depois
   `SET SHOWPLAN_TEXT OFF`.
3. Leia `plan[]` — lista de linhas do plano textual.
4. Identifique gargalos: Table Scan (sem índice), Hash Match (sort custoso),
   Sort + Spill.

## RUBRICA / REGRAS DE DECISÃO
- Table Scan em tabela grande → falta índice; recomende coluna para indexar.
- Hash Match em join → join sem índice de suporte; avalie chave de join.
- Nested Loops em tabela grande → pode ser lento; recomende filtro mais seletivo.
- Se o runner retornar erro de batch → reporte e sugira simplificar a query
  (subqueries complexas podem não ser suportadas por SHOWPLAN_TEXT em alguns
  ambientes).

## SAÍDA
Linhas do plano em bloco de código + leitura de gargalos encontrados.
Nota: "Este é um plano estimado — não reflete dados reais executados."

## NÃO FAÇA
- Não execute a query de fato; este é apenas o plano estimado.
- Não contorne erros de SHOWPLAN forçando execução real.
