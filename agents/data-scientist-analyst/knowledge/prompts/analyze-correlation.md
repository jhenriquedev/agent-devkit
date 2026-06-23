# analyze-correlation

## Objetivo
Calcular correlacoes lineares de Pearson entre colunas numericas e identificar
pares relevantes, com declaracao explicita de que correlacao nao implica
causalidade.

## Entradas
- `--source` (obrigatorio).
- `--columns`: lista de colunas numericas (default: todas numericas).
- `--max-rows`, `--max-file-mb`: controles.

## Raciocinio
1. Confirme sha256, row_count, truncated, warnings.
2. Calcule matriz de correlacao de Pearson para colunas numericas.
3. Priorize pares com |r| >= 0.7 (forte), 0.4–0.7 (moderada), < 0.4 (fraca).
4. Para cada par relevante, apresente r, interpretacao e ressalva de nao-
   causalidade.
5. Sinalize pares suspeitos de multicolinearidade para uso em modelagem.

## Rubrica de decisao
- |r| alto -> "hipotese de associacao forte", nao "causa".
- Base truncada -> correlacoes sao indicativas, nao definitivas.
- n < 30 por par -> resultado fragil; sinalize.

## Saida
Tabela de pares relevantes (coluna_a, coluna_b, r, interpretacao), heatmap
textual simplificado, aviso de nao-causalidade, bloco de rastreabilidade.

## Nao fazer
- Nao apresentar correlacao como causalidade em nenhuma circunstancia.
- Nao ignorar tamanho da amostra ao interpretar r.
- Nao calcular Pearson em colunas nao-numericas sem aviso.
