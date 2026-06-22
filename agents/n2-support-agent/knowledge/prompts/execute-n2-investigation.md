# Execute N2 Investigation

## Objetivo

Orquestrar o runbook N2 completo em um contrato unico.

## Entradas

- Card Azure ou fixture.
- Contrato N1 opcional.
- `--codebase-path`.
- Destino `--output` ou card Azure.
- `--execute` para mutacoes.

## Raciocinio

1. Carregue contexto.
2. Valide handoff N1.
3. Analise codigo.
4. Correlacione evidencia runtime.
5. Classifique causa raiz.
6. Gere patch plan.
7. Revise readiness.
8. Planeje ou execute automacoes Azure.

## Rubrica/Regras

- Sem destino, readiness bloqueia.
- Mutacao Azure exige `--execute`.
- Nao pule handoff nem mascaramento.

## Saida

JSON `n2-investigation.json` com contexto, codigo, correlacao, causa raiz,
plano, acoes Azure, artefatos e auditoria.

## Nao faca

- Nao implementar patch.
- Nao executar mutacao sem `--execute`.
