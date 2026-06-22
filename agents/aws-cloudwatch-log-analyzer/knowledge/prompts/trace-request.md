# Prompt: Trace Request

## Objetivo

Rastrear a linha do tempo de um request por identificador tecnico em eventos do
CloudWatch Logs.

## Entradas

- `identifier`: request id, correlation id, trace id ou valor tecnico similar.
- `identifier_type`: tipo do identificador.
- `region`, `log_group`, `start_time`, `end_time`: escopo CloudWatch.
- `limit`: limite da timeline.

## Regras

- Prefira identificadores tecnicos nao sensiveis.
- Rejeite ou mascare PII, token, segredo, CPF, e-mail completo ou payload bruto.
- Ordene eventos por timestamp.
- Destaque eventos de erro sem inferir eventos ausentes.
- Mantenha a janela restrita ao fluxo investigado.

## Saida

- Mostre tipo e valor mascarado quando necessario.
- Informe total de eventos e eventos com erro.
- Renderize timeline em ordem cronologica.
- Liste lacunas sobre outros log groups ou sistemas envolvidos.

## Nao faca

- Nao usar dado pessoal como chave de busca quando houver alternativa tecnica.
- Nao reproduzir tokens ou segredos.
- Nao afirmar caminho completo se parte do fluxo nao foi consultada.
