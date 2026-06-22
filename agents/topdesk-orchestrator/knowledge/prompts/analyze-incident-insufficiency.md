# Analyze Incident Insufficiency

## Objetivo

Avaliar se um incidente tem insumo suficiente para ser trabalhado e gerar
perguntas objetivas.

## Entradas

- `id` ou `number`.
- `fixture` com incidente.

## Raciocinio

1. Leia resumo, request, categoria e prioridade.
2. Aplique `knowledge/triage-rules.md`.
3. Verifique sintoma, sistema afetado, evidencia e impacto.
4. Gere uma pergunta para cada lacuna real.
5. Atribua confianca conforme quantidade e severidade das lacunas.

## Rubrica

- Insuficiente quando falta sintoma claro, sistema afetado ou evidencia.
- Nao marque insuficiente apenas por texto curto se o conteudo for claro.
- Perguntas devem ser especificas e acionaveis.

## Saida

Indicador de insuficiencia, confianca, campos faltantes e perguntas sugeridas.

## Nao faca

Nao escrever no chamado. Nao perguntar o que o texto ja responde. Nao inventar
categoria.
