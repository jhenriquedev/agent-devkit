# detect-outliers

## Objetivo
Detectar valores atipicos (outliers) por coluna usando IQR, z-score ou ambos,
classificando cada outlier para orientar acao.

## Entradas
- `--source` (obrigatorio).
- `--columns`: colunas numericas a analisar.
- `--method {iqr|zscore|both}` (default: iqr).
- `--threshold`: fator IQR (default 1.5) ou z limiar (default 3.0).
- `--max-rows`, `--max-file-mb`: controles de leitura.

## Raciocinio
1. Confirme sha256 e warnings.
2. Escolha metodo:
   - IQR: preferivel para distribuicoes assimetricas ou robustez.
   - z-score: adequado para distribuicoes proximas do normal.
3. Para cada outlier detectado, classifique:
   - "erro provavel" (valor impossivel dado dominio),
   - "evento raro" (extremo mas plausivel),
   - "investigar" (incerto).
4. Reporte contagem, percentual e exemplos mascarados se PII presente.

## Rubrica de decisao
- IQR e preferivel por padrao; z-score so quando distribuicao e claramente normal.
- truncated=true -> outliers detectados sao "parciais"; declare.
- PII em coluna de outlier -> mascare exemplos.

## Saida
Tabela: coluna, metodo, n_outliers, pct_outliers, limites, exemplos_mascarados,
classificacao. Resumo de acao recomendada por tipo.

## Nao fazer
- Nao remover outliers — somente identificar e classificar.
- Nao concluir sobre integridade da base sem profile.
- Nao exibir PII integral em exemplos.
