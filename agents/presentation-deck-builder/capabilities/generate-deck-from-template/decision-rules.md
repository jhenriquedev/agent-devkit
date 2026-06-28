# Decision Rules

- Gerar deck somente a partir de template resolvido e versao existente.
- Se `template_version` nao for informado, usar `current_version`.
- Exigir template validado para geracao sem perguntas adicionais.
- Validar entrada estruturada contra `input-schema` e `slide-map` antes de renderizar.
- Quando conteudo obrigatorio estiver ausente ou ambiguo, pedir esclarecimento antes de gerar.
- Preservar identidade visual, layouts, placeholders e hierarquia visual do template.
- Nao inventar dados de negocio, metricas, conclusoes ou imagens ausentes.
- Escrever apenas no `output` solicitado ou no destino padrao de decks gerados.
- Sem `@oai/artifact-tool`/presentations skill disponivel, falhar com mensagem acionavel sem simular PPTX.
- Revisar overflow, placeholders vazios e slides superlotados antes da entrega.
