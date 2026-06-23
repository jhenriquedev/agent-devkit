# Prompt: Estimate Blast Radius

## Objetivo
Estimar o impacto de falha ou alteracao de um recurso, listando dependentes
diretos e indiretos e as incertezas envolvidas.

## Entradas esperadas
- resource_id (obrigatorio), inventory.json, dependency_map.json (opcional;
  derivado do inventario se ausente).

## Passos de raciocinio
1. Localize o recurso alvo no inventario.
2. Percorra o grafo reverso: dependentes diretos (arestas que apontam para ele)
   e indiretos (transitivos).
3. Pondere a confianca: dependentes via arestas inferidas tem incerteza maior.
4. Liste acoes inseguras e o que precisa ser confirmado antes de qualquer
   mudanca.

## Regras de decisao
- Se houver dependencias nao resolvidas relacionadas ao alvo, o impacto pode
  estar SUBESTIMADO — declare isso explicitamente.
- Recurso alvo nao encontrado => pare e reporte; nao retorne blast radius vazio
  como se fosse seguro.

## Formato de saida
- blast-radius.md (diretos, indiretos, incertezas, acoes inseguras),
  blast-radius.json.

## Nao faca
- Nao conclua "impacto baixo" com dependencias nao resolvidas em aberto.
