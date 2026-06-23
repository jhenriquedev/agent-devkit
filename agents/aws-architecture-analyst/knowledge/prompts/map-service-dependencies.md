# Prompt: Map Service Dependencies

## Objetivo
Construir um grafo de dependencias entre recursos do inventario, com confianca
por aresta, separando dependencias resolvidas das nao resolvidas.

## Entradas esperadas
- inventory.json (obrigatorio).

## Passos de raciocinio
1. Para cada recurso, leia `relationships` (ja vem com type/confidence/evidence).
2. Uma aresta e RESOLVIDA se o target existe no inventario ou e um ARN valido;
   senao e NAO RESOLVIDA.
3. Preserve `confidence` (confirmed|inferred). Nao promova inferencia a fato.
4. Destaque dependencias nao resolvidas como risco de mapa incompleto.

## Regras de decisao
- confirmed: veio direto de um campo da AWS (ex.: Lambda Role).
- inferred: deduzida por convencao/nome — sempre rotular como tal.
- Target fora do inventario e nao-ARN => unresolved (provavel recurso fora do
  escopo coletado).

## Formato de saida
- dependency-map.json (nodes, edges, edge_count, unresolved_dependencies),
  dependency-map.md, unresolved-dependencies.json.

## Nao faca
- Nao invente arestas sem evidencia. Nao trate unresolved como inexistente.
