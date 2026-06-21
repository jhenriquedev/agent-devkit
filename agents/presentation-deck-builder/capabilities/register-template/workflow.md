# Workflow: Register Template

1. Validar arquivo `.pptx`, `.ppt` ou `.potx`.
2. Perguntar antes de salvar quando `--yes-save` nao for informado.
3. Criar `templates/<template-id>/versions/<version>/`.
4. Copiar o arquivo como `template.pptx`.
5. Criar `template.yaml`, `slide-map.yaml`, schemas de entrada e changelogs.
6. Definir `current_version` somente para status `validated`.
