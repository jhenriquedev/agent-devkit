# Update Azure Workflow

## Objetivo

Planejar ou executar automacoes Azure de apoio ao N2.

## Entradas

- `--project` e `--card`.
- Patch plan gerado ou destino.
- `--execute`.
- Estado, coluna ou responsavel quando informados.

## Raciocinio

1. Sempre planeje tag `Analise N2`.
2. Gere comentario tecnico.
3. Anexe patch plan quando houver arquivo.
4. Planeje movimento somente com estado alvo.
5. Inclua coluna apenas junto do estado.
6. Execute apenas com `--execute`.

## Rubrica/Regras

- Sem `--execute`, modo e `dry_run`.
- Acao sem parametro obrigatorio vira `skipped`.
- Falha de Azure vira status `failed`.

## Saida

JSON com `azureActions`, cada acao contendo agente, capability, modo, status,
resumo e command preview.

## Nao faca

- Nao mover card sem estado.
- Nao executar escrita sem confirmacao.
