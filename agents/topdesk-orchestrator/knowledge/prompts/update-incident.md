# Update Incident

## Objetivo

Atualizar campos controlados de um incidente TOPdesk com dry-run por padrao.

## Entradas

- `id` ou `number`.
- `fields_json`.
- `execute`, `fixture`, `output`.

## Raciocinio

1. Exija alvo explicito por ID ou numero.
2. Liste cada campo de `fields_json`.
3. Bloqueie campos unsupported antes de chamar o repository.
4. Mostre dry-run e instrucao de reexecucao.
5. Execute apenas com `--execute`.

## Rubrica

- Bloquear `request`, fechamento, resolucao, arquivamento e escalonamento.
- Alteracoes devem ser pontuais e justificaveis.
- Payload em massa ou ambiguo deve ser recusado.

## Saida

Alvo, campos planejados, dry-run e proxima acao.

## Nao faca

Nao sobrescrever a solicitacao original. Nao fechar ou arquivar chamado. Nao
executar sem confirmacao.
