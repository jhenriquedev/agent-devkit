# Prompt: Detect Error Patterns

## Objetivo
Detectar fingerprints de erro recorrentes e sua distribuição relevante nos logs.

## Entradas esperadas
- Obrigatórias: `--source`, `--from`, `--to`. Opcionais: `--service`, `--level`
  (default "error"), `--query`, `--limit`.

## Raciocínio
1. Colete eventos de erro bounded.
2. Normalize mensagens em fingerprints (números -> <num>, hex -> <hex>) e conte repetições.
3. Quando útil, descreva a distribuição no tempo (timeline) para ver se é pico ou contínuo.
4. Liste os top padrões + uma amostra representativa por padrão.

## Regras de decisão
- Fingerprints são heurística, não fato — rotule. Ver também: decision-rules.md.
- Preserve evidência de amostra para cada padrão de topo.
- Não superestime causa-raiz; "frequente" != "culpado".

## Formato de saída
Cabeçalho + "Top Patterns" (com contagem) + "Samples".

## Não fazer
- Não colapsar mensagens semanticamente distintas só porque o texto é parecido.
- Não omitir o tamanho da amostra analisada.
