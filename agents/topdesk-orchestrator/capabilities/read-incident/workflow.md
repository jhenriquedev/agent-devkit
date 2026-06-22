# Read Incident Workflow

## Fluxo

1. Receber `--id` ou `--number`, ou fixture.
2. Bloquear execucao real sem identificador.
3. Ler incidente por ID ou numero.
4. Carregar progress trail somente com `--include-progress-trail`.
5. Normalizar campos para resumo humano.
6. Renderizar solicitacao original.
7. Limitar progress trail a 20 entradas.

## Saida

Retorna `incident.md`.
