# Workflow: Comentar Card

## Objetivo

Gerar um comentario adequado ao card e executar a escrita somente depois de
confirmacao.

## Passos

1. Validar `work_item_id` e intencao do comentario.
2. Ler o card com `get-work-item`.
3. Gerar comentario proposto.
4. Apresentar alvo, comentario e risco.
5. Pedir confirmacao explicita.
6. Se confirmado, executar `add-comment`.
7. Informar resultado e ID/URL do comentario quando disponivel.

## Bloco de confirmacao

```text
Alvo: <work-item-id>
Acao: adicionar comentario
Comentario:
<texto>
Risco: baixo|medio|alto
Confirmar execucao? sim/nao
```

## Guardrails

- Nao comentar sem confirmacao.
- Nao incluir dados sensiveis nao solicitados.
- Nao escrever em nome de outra pessoa.
- Nao afirmar que uma acao foi executada antes da resposta do method.
