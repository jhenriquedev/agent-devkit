# Regras

- Usar forecast baseline por media movel; nao apresentar como modelo preditivo robusto.
- Declarar `window`, `periods`, granularidade e historico usado.
- Nao extrapolar alem dos periodos solicitados.
- Reportar series curtas, dados ausentes e mudancas estruturais como limitacoes.
- Separar valores observados de valores projetados.
- Nao usar forecast para decisao automatica sem revisao humana.
