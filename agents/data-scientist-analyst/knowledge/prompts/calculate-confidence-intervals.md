# calculate-confidence-intervals

## Objetivo
Calcular intervalo de confianca para a metrica especificada e interpretar sua
amplitude em relacao a decisao pratica.

## Entradas
- `--source` (obrigatorio).
- `--metric-column` (obrigatorio): coluna numerica.
- `--confidence`: nivel de confianca (default 0.95).
- `--group-column`: calcular IC por grupo se informado.

## Raciocinio
1. Confirme sha256, warnings, n da amostra.
2. Calcule media, erro padrao, IC (lower, upper) para o nivel de confianca.
3. Declare assumptions: aproximacao normal (adequada para n >= 30).
4. Interprete amplitude do IC em linguagem pratica: estreito (precisao alta)
   vs largo (incerteza alta / amostra insuficiente).
5. Se grupo informado, reporte IC por grupo e compare amplitudes.

## Rubrica de decisao
- n < 30 -> IC e aproximado (assunção normal fragilizada); declare.
- IC muito largo -> "incerteza alta; considere ampliar amostra".
- validity_warnings presente -> destaque impacto no IC.

## Saida
Media, n, erro_padrao, IC_lower, IC_upper, interpretacao de amplitude, assumptions,
limitacoes, bloco de rastreabilidade.

## Nao fazer
- Nao interpretar IC como "probabilidade de o valor estar nesse intervalo" — e
  frequentista (confianca no metodo, nao na estimativa pontual).
- Nao ignorar n pequeno ao interpretar IC.
- Nao reportar IC sem amplitude interpretada.
