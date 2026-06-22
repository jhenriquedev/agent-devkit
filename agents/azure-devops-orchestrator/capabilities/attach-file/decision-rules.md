# Decision Rules: Anexar Arquivo

- Validar que o arquivo existe localmente antes de ler ou escrever no Azure.
- Sempre ler o card alvo antes de preparar o plano de anexo.
- Mostrar path, nome do arquivo, comentario e card alvo antes da escrita real.
- Nao anexar dados sensiveis sem solicitacao explicita do usuario.
- Sem `--execute`, retornar apenas plano de escrita em dry-run.
- Com `--execute`, fazer upload e adicionar relacao `AttachedFile`.
- Nao enviar arquivo diferente do path informado pelo usuario.
