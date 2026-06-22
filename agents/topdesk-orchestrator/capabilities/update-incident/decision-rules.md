# Decision Rules - update-incident

- `update-incident` exige ID, numero ou fixture e `fields_json`.
- Validar campos antes de chamar o repository.
- Bloquear `request`, fechamento, resolucao, arquivamento e escalonamento.
- Dry-run e obrigatorio por padrao.
- Escrita real exige `--execute`.
- Campos devem ser minimos e revisaveis.
- Nao fazer update em massa.
- Erro de validacao deve explicar o campo unsupported.
