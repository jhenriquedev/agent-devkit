# calculate-sample-size

## Objetivo
Calcular tamanho de amostra necessario para detectar um efeito minimo com
poder e significancia especificados.

## Entradas
- `--baseline-rate`: taxa ou media baseline do grupo controle.
- `--minimum-detectable-effect` (MDE): diferenca minima relevante a detectar.
- `--alpha`: nivel de significancia (default 0.05).
- `--power`: poder do teste (default 0.80).
- `--two-tailed`: teste bicaudal (default true).

## Raciocinio
1. Declare os parametros recebidos: baseline, MDE, alpha, power.
2. Calcule n por grupo usando formula de aproximacao normal.
3. Calcule tamanho de efeito (Cohen's d ou equivalente) dado MDE e baseline.
4. Interprete: n pequeno com MDE grande (facil de detectar) vs n grande com MDE
   pequeno (teste sensivel).

## Rubrica de decisao
- MDE muito pequeno -> n pode ser inviavel; sinalize e sugira rever MDE.
- power < 0.80 -> risco de falso negativo alto; recomende 0.80–0.95.
- Resultado e baseado em aproximacao normal; declare.

## Saida
n_por_grupo, n_total, tamanho_efeito, interpretacao, parametros usados,
limitacoes (aproximacao normal), bloco de rastreabilidade.

## Nao fazer
- Nao calcular sem declarar todos os parametros assumidos.
- Nao ignorar impacto do MDE na viabilidade do experimento.
- Nao recomendar n sem mencionar o poder associado.
