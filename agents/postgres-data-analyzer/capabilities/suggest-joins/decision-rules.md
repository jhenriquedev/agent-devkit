# Decision Rules: Suggest Joins

- Sugerir joins a partir de FKs, nomes de colunas, tipos compativeis e contexto de schema.
- Diferenciar join declarado por FK de join inferido por heuristica.
- Nao consultar valores brutos para validar join sem necessidade explicita e limite seguro.
- Atribuir confianca alta, media ou baixa com justificativa.
- Nao gerar query final que exponha dados pessoais sem mascaramento ou agregacao.
- Evitar joins cartesianos e joins sem predicado claro.
- Registrar riscos de cardinalidade e duplicacao de linhas.
- A saida deve alimentar `build-analysis-query` e ERD, nao executar consultas.
