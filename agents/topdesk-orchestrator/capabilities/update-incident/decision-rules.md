# Decision Rules - update-incident

- `update-incident` exige ID, numero ou fixture e `fields_json`.
- Validar campos antes de chamar o repository.
- Bloquear `request`, fechamento, resolucao, arquivamento e escalonamento.
- Dry-run e obrigatorio por padrao.
- Escrita real exige `--execute`.
- Campos devem ser minimos e revisaveis.
- Nao fazer update em massa.
- Erro de validacao deve explicar o campo unsupported.
- Nunca enviar campo `request`; preservar solicitacao original.
- Bloquear aliases de fechamento/resolucao como `statusName`, `statusId` e `processingStatus` quando indicarem encerramento.
- Nao aceitar update sem alvo explicito por ID, numero ou fixture controlada.
- `fields_json` deve ser objeto JSON, nao lista ou string livre.
- Em dry-run, renderizar target, campos planejados e risco sem escrita real.
- Em execucao real, relatar resultado resumido sem despejar resposta sensivel.
