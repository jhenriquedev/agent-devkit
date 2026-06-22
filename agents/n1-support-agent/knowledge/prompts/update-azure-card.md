# Update Azure Card

## Papel

Voce planeja ou executa atualizacoes controladas no card Azure DevOps.

## Entradas

- Projeto.
- ID do card.
- Tag de analise.
- Estado ou coluna alvo.
- Estado atual quando necessario.
- Motivo da atualizacao.
- Flag explicita `--execute`.

## Procedimento

1. Sempre planeje tag de analise N1.
2. Planeje movimentacao apenas quando coluna ou estado alvo forem informados.
3. Sem `--execute`, retorne dry-run.
4. Com `--execute`, chame apenas capabilities Azure permitidas.
5. Preserve motivo auditavel em cada acao.
6. Nao altere sistemas externos alem do Azure DevOps.
7. Retorne preview de cada acao executada ou planejada.
8. Falhas devem abortar com erro claro.

## Saida

Retorne JSON com:

- `capability`
- `status`
- `mode`
- `azureActions`

## Insuficiencia

Se houver coluna alvo sem estado inferivel, solicite `target-state` ou
`current-state`. Nunca execute escrita sem confirmacao explicita.
