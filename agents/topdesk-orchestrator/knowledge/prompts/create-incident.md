# Create Incident

## Objetivo

Planejar e, sob confirmacao, criar um incidente TOPdesk com dry-run por padrao.

## Entradas

- `brief_description` e `request`.
- `caller_id`, `category`, `priority`, `operator_group`, `fields_json`.
- `execute`, `fixture`, `output`.

## Raciocinio

1. Garanta resumo util e request com contexto suficiente.
2. Se faltar contexto, pare e recomende `analyze-incident-insufficiency`.
3. Use catalogo e busca de pessoas quando precisar validar campos controlados.
4. Monte payload minimo e revisavel.
5. Rode dry-run primeiro; use `--execute` apenas com confirmacao humana.

## Rubrica

- Campo obrigatorio ausente bloqueia criacao.
- Categoria, prioridade e grupo precisam de evidencia ou catalogo.
- Suspeita de duplicidade deve ser sinalizada antes da criacao.

## Saida

Payload planejado, dry-run e numero do incidente quando criado.

## Nao faca

Nao invente solicitante. Nao preencher fechamento/resolucao. Nao executar sem
confirmacao.
