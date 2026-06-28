# Decision Rules

- Registrar apenas arquivos `.pptx`, `.ppt` ou `.potx` recebidos ou indicados pelo usuario.
- Perguntar antes de salvar em `templates/` quando `--yes-save` nao estiver presente.
- Criar estrutura completa: `template.yaml`, `versions/<version>/template.pptx`, schemas, slide-map, usage notes e changelog.
- Nunca sobrescrever template ou versao existente sem decisao explicita e segura.
- Marcar template como `draft` por padrao; `current_version` so deve apontar para versao validada.
- Normalizar `template_id` em kebab-case e paths relativos portaveis.
- Validar que o arquivo de origem existe e e um pacote PowerPoint plausivel antes de copiar.
- Nao inferir campos de entrada obrigatorios sem inspecao suficiente; registrar lacunas.
- Preservar o arquivo original e copiar para a estrutura versionada.
- Atualizar catalogo apenas quando a politica de escrita permitir.
