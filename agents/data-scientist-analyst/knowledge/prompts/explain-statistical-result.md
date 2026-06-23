# explain-statistical-result

## Objetivo
Traduzir resultado estatistico tecnico (p-valor, IC, d, n) em linguagem acessivel
para decisao executiva, sem perder rigor nem ocultar limitacoes.

## Entradas
- `--p-value`: valor-p do teste.
- `--alpha`: nivel de significancia usado.
- `--effect-size`: Cohen's d ou equivalente.
- `--confidence-interval`: (lower, upper) se disponivel.
- `--n`: tamanho da amostra.
- `--context`: descricao do problema de negocio.

## Raciocinio
1. Declare o resultado tecnico exato (p, alpha, d, IC, n).
2. Traduza cada numero:
   - p < alpha: "a diferenca observada e improvavel por acaso dado alpha".
   - d: magnitude pratica da diferenca.
   - IC: faixa de incerteza da estimativa.
3. Combine em uma frase executiva clara.
4. Liste limitacoes e assumptions declaradas.

## Rubrica de decisao
- p < alpha sem effect size informado -> solicite ou declare como limitacao.
- n baixo -> destaque fragilidade da conclusao.
- Resultado ambiguo (p proximo de alpha) -> declare inconclusivo.

## Saida
Resultado tecnico (todos os numeros), traducao executiva em 2-3 frases, limitacoes,
recomendacoes de proximo passo.

## Nao fazer
- Nao simplificar a ponto de omitir limitacoes.
- Nao concluir causalidade ao explicar o resultado.
- Nao usar jargao sem traducao para o publico-alvo.
