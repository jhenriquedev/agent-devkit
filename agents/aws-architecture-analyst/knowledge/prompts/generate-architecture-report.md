# Prompt: Generate Architecture Report

## Objetivo
Consolidar inventario, dependencias e revisoes num relatorio arquitetural
acionavel que separe fatos, inferencias e perguntas abertas.

## Entradas esperadas
- inventory.json (obrigatorio), dependency_map.json (opcional).

## Passos de raciocinio
1. Resuma escopo (account, region, fonte) e contagem por servico.
2. Liste recursos-chave e dependencias mapeadas (com confianca).
3. Consolide achados das reviews disponiveis; gere acoes recomendadas.
4. Reuna todas as perguntas abertas e lacunas num bloco proprio.

## Regras de decisao
- O relatorio nunca recomenda mutar AWS diretamente; recomenda investigacao/
  validacao humana.
- Toda recomendacao deve apontar a evidencia (recurso/aresta/finding).

## Formato de saida
- architecture-report.md, executive-summary.md, recommended-actions.md,
  open-questions.md.

## Nao faca
- Nao misture fato e inferencia no mesmo paragrafo sem rotular. Nao oculte
  lacunas para parecer mais completo.
