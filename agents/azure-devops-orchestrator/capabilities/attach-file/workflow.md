# Workflow

1. Receber `project`, `id` e path do arquivo.
2. Validar que o arquivo existe.
3. Ler o card alvo.
4. Sem `--execute`, renderizar plano de anexo.
5. Com `--execute`, fazer upload do arquivo e adicionar relacao `AttachedFile`.
