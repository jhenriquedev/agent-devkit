# Request More Info Workflow

## Fluxo

1. Receber ID, numero ou fixture.
2. Ler o incidente.
3. Rodar analise de insuficiencia.
4. Montar mensagem com perguntas faltantes.
5. Criar payload de `action`, nunca de `request`.
6. Validar payload contra campos unsupported.
7. Atualizar em dry-run por padrao.
8. Renderizar payload planejado e perguntas.

## Saida

Retorna `request-more-info-plan.md`.
