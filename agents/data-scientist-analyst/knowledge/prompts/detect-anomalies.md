# detect-anomalies

## Objetivo
Detectar pontos anomalos em serie temporal por z-score, classificando cada
anomalia como observada e propondo hipoteses (nao causas).

## Entradas
- `--source` (obrigatorio).
- `--date-column`, `--metric-column` (obrigatorios).
- `--threshold`: limiar z-score (default 3.0).
- `--granularity`: agregacao da serie.

## Raciocinio
1. Confirme sha256, warnings, n_periodos.
2. Calcule z-score por ponto; classifique como anomalia se |z| > threshold.
3. Para cada anomalia: data, valor, z-score, direcao (acima/abaixo da media).
4. Se serie curta (< ~14 pontos): z-score e pouco confiavel; declare.
5. Apresente hipoteses (nao causas) para investigacao.

## Rubrica de decisao
- Serie curta -> rebaixe anomalias a "indicativas".
- threshold padrao 3.0 gera poucos falsos positivos; 2.0 e mais sensivel.
- truncated=true -> anomalias em periodos truncados podem estar ausentes.

## Saida
Lista de anomalias (data, valor, z_score, direcao), estatisticas da serie
(media, desvio), hipoteses de investigacao, limitacoes, bloco de
rastreabilidade.

## Nao fazer
- Nao atribuir causa a anomalias; somente identificar e propor hipoteses.
- Nao usar z-score em serie muito curta sem ressalva.
- Nao ignorar direcao (alta vs baixa) no relato.
