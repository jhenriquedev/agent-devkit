# Prompt: Generate Log Report

## Objetivo
Gerar um relatório operacional em Markdown a partir dos logs: contagens, distribuições,
amostras e próximos passos de investigação.

## Entradas esperadas
- Obrigatórias: `--source`, `--from`, `--to`. Opcionais: `--query`, `--service`,
  `--environment`, `--level`, `--limit`.

## Raciocínio
1. Conte os eventos que casam (count_events) — esse é o total de fato.
2. Carregue amostras bounded para evidência.
3. Quando possível, agregue por level/service e por timeline para a seção de distribuição.
4. Sintetize: escopo exato, resumo (total vs. amostras vs. limite atingido), padrões,
   amostras e próximos passos.

## Regras de decisão
- Separe claramente: contagens (fato), amostras (fato) e padrões (inferência). Ver também: decision-rules.md.
- Declare a fonte e a janela exatas.
- Se o limite foi atingido, diga que o conjunto pode estar truncado.

## Formato de saída
Seções: Scope, Summary (matching events / loaded samples / limit reached), Patterns,
Samples, Next Steps.

## Não fazer
- Não apresentar contagem da amostra carregada como se fosse o total real.
- Não recomendar ações sem ligá-las a um padrão ou contagem observada.
