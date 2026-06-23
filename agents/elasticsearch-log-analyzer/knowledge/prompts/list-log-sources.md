# Prompt: List Log Sources

## Objetivo
Descobrir quais indices, data streams e aliases existem e podem virar `--source`,
filtrando por um pattern opcional. É o passo de descoberta antes de qualquer busca.

## Entradas esperadas
- `--pattern` (opcional, ex.: "logs-*"); `--limit` (opcional, default 100).
- Sem pattern, lista tudo (pode ser grande — prefira sempre um pattern).

## Raciocínio
1. Se o usuário não sabe o source exato, ofereça um pattern derivado do serviço/ambiente
   mencionado (ex.: "checkout em prod" -> `logs-prod-*` ou `*checkout*`).
2. Rode list-log-sources com esse pattern.
3. Agrupe a saída em Indices, Data Streams e Aliases.

## Regras de decisão
- Pattern é só filtro de runtime; nunca o persista como default. Ver também: decision-rules.md.
- Mantenha a saída compacta (só nomes e metadados básicos).
- Se a lista vier vazia, sugira afrouxar o pattern (ex.: trocar `logs-prod-*` por `*`).

## Formato de saída
Markdown com seções Indices / Data Streams / Aliases (ver template). Indique o pattern usado.

## Não fazer
- Não inferir projeto a partir do `.env`.
- Não escolher um source automaticamente sem confirmar com o usuário se houver ambiguidade.
