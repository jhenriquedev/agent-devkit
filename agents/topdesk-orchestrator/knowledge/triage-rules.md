# TOPdesk Triage Rules

## Objetivo

Definir regras de suficiencia, categoria e prioridade para triagem de incidentes
TOPdesk sem depender de achismo.

## Suficiencia

Um incidente e insuficiente quando falta qualquer item abaixo:

- Sintoma claro: o que falha, para quem e em qual fluxo.
- Sistema ou servico afetado.
- Evidencia identificavel: mensagem de erro, print, request id, numero de pedido,
  ativo ou horario aproximado.
- Impacto: individual, equipe, area inteira ou operacao critica.

## Categoria

- Use somente valores presentes no catalogo TOPdesk carregado.
- Sinais de `Software`: portal, sistema, aplicacao, erro HTTP, API, tela.
- Sinais de `Acesso`: login, senha, autenticacao, permissao, usuario bloqueado.
- Sinais de `Hardware`: notebook, computador, impressora, periferico.
- Sem correspondencia sustentada, deixe categoria a confirmar.

## Prioridade

- P1: operacao critica parada, muitos usuarios ou indisponibilidade geral.
- P2: equipe ou area relevante impactada com degradacao operacional.
- P3: usuario individual bloqueado em atividade importante.
- P4: solicitacao comum, duvida, melhoria ou baixo impacto.

## Solicitante

- Preencha `caller` somente quando `search-persons` retornar uma pessoa claramente
  correspondente ao nome do chamado.
- Se houver multiplas pessoas plausiveis, nao escolher automaticamente.

## Escrita

- O plano de update deve incluir apenas campos justificados por evidencia.
- Nunca alterar `request`, status de fechamento, resolucao, arquivamento ou
  escalonamento.
