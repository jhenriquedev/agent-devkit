# Decision Rules

- Inspecionar somente template e versao resolvidos pelo catalogo.
- Ler layouts, placeholders, slide types, schema, slide-map e usage notes quando existirem.
- Nao modificar template, manifest ou artefatos durante inspecao.
- Identificar campos obrigatorios, opcionais, repetiveis e restricoes visuais.
- Registrar lacunas de template: placeholders sem nome, slide-map ausente, schema incompleto ou status incoerente.
- Diferenciar problemas bloqueantes de recomendacoes de melhoria.
- Nao declarar template validado apenas por conseguir abrir o arquivo.
- Preservar paths relativos e portaveis no relatorio.
- A saida deve orientar geracao de input, plano de deck ou refinamento.
- Se a versao nao existir, retornar erro acionavel sem fallback silencioso.
