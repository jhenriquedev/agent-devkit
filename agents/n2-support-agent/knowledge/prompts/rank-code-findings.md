# Rank Code Findings

## Objetivo

Ordenar achados para que o patch ataque implementacao antes de testes.

## Entradas

- Resultado de `analyze-code-root-cause`.
- `technicalFindings` com `fileKind`, `score` e caminho.

## Raciocinio

1. Separe achados por tipo de arquivo.
2. Aplique a prioridade source, migration, test, support.
3. Dentro do mesmo tipo, use maior score primeiro.
4. Em empate, ordene por caminho para estabilidade.
5. Atribua `rank` sequencial a cada achado.

## Rubrica/Regras

- `source` tem prioridade 0.
- `migration` tem prioridade 1.
- `test` tem prioridade 2.
- `support` tem prioridade 3.

## Saida

JSON com `rankedFindings`, mantendo os campos originais e adicionando `rank`.

## Nao faca

- Nao promova teste a alvo primario sem source.
- Nao remova evidencia original do achado.
