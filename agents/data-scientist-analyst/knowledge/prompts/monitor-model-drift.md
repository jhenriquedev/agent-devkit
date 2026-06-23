# monitor-model-drift

## Objetivo
Comparar distribuicao de features entre dataset de referencia e amostra atual
para detectar drift e recomendar reavaliacao do modelo.

## Entradas
- `--source` (obrigatorio): amostra atual.
- `--reference-source` (obrigatorio): dataset de referencia (treino ou periodo
  anterior).
- `--feature-columns`: features a monitorar.
- `--target-column`: alvo (para verificar drift de distribuicao do alvo).

## Raciocinio
1. Confirme sha256 de ambas as fontes; registre ambas no bloco de rastreabilidade.
2. Para cada feature: compare media, desvio, min, max entre referencia e atual.
3. Calcule deslocamento relativo (delta_media / desvio_referencia).
4. Classifique: sem drift, drift moderado (> 0.5 sigma), drift alto (> 1.0 sigma).
5. Se drift alto em feature importante -> recomende reavaliacao do modelo.

## Rubrica de decisao
- Drift alto em feature principal -> "modelo pode estar desatualizado; reavaliar".
- Drift no alvo -> distribuicao mudou; retreinamento urgente.
- Ambas as fontes devem ter sha256; sem sha256 -> resultado inutilizavel.

## Saida
Tabela por feature (delta_media, delta_relativo, classificacao), resumo do drift
geral, recomendacao, bloco de rastreabilidade (ambas as fontes).

## Nao fazer
- Nao comparar fontes sem sha256 registrado de ambas.
- Nao ignorar drift no alvo.
- Nao reportar drift sem recomendar acao.
