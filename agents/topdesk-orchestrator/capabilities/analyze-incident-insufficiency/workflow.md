# Analyze Incident Insufficiency Workflow

## Fluxo

1. Receber ID, numero ou fixture.
2. Carregar incidente.
3. Aplicar fallback deterministico `analyze_insufficiency`.
4. Avaliar resumo, request, categoria, prioridade e evidencia especifica.
5. Gerar campos faltantes sem duplicidade.
6. Gerar perguntas especificas.
7. Renderizar confianca e perguntas.

## Saida

Retorna `incident-insufficiency-analysis.md`.
