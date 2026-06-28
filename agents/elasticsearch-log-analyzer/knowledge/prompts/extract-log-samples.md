# Prompt: Extract Log Samples

## Objetivo
Extrair amostras de log representativas e limitadas para investigação, relatórios ou
tickets externos.

## Entradas esperadas
- Obrigatórias: `--source`, `--from`, `--to`. Opcionais: `--query`, `--service`,
  `--level`, `--limit` (default 20).

## Raciocínio
1. Busque eventos no escopo e filtros pedidos.
2. Selecione até `--limit` amostras representativas (diversidade de serviço/level/trace
   quando possível).
3. Renderize timestamp, service, level, trace, message e id.

## Regras de decisão
- Amostras sempre bounded. Ver também: decision-rules.md.
- Mantenha event ids quando disponíveis (úteis para `get-event` posterior).
- Se houver segredo, token, API key, Authorization ou payload sensível, sinalize sem reproduzir o valor.

## Formato de saída
Cabeçalho (source/quantidade) + tabela de amostras.

## Não fazer
- Não copiar segredos visíveis no payload para o ticket; sinalize sem reproduzir.
- Não ultrapassar o limite pedido.
