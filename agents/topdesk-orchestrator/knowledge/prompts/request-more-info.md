# Request More Info

## Objetivo

Preparar uma solicitacao de informacoes faltantes sem sobrescrever o `request`
original do incidente.

## Entradas

- `id` ou `number`.
- `execute`, `fixture`, `output`.

## Raciocinio

1. Leia o incidente.
2. Rode a analise de insuficiencia.
3. Se nao houver lacunas, nao envie pedido.
4. Monte nota ou acao adicional com perguntas numeradas.
5. Use dry-run por padrao; execute apenas com confirmacao.

## Rubrica

- O payload nunca pode conter `request`.
- Perguntas devem sair da analise de lacunas.
- O tom deve ser operacional e claro para o solicitante.

## Saida

Incidente alvo, dry-run, payload planejado de nota/acao e perguntas.

## Nao faca

Nao substituir a solicitacao original. Nao enviar pedido sem lacunas. Nao executar
sem `--execute`.
