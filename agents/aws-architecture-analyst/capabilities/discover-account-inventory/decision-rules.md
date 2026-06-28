# Decision Rules: Discover Account Inventory

## Objetivo de decisao

Executar coleta read-only de inventario AWS somente quando o escopo estiver
claro o suficiente para produzir artefatos rastreaveis: `inventory.json`,
`inventory-summary.md` e `collection-metadata.json`.

## Entradas minimas

- Usar `--fixture` quando a execucao for teste, revisao local ou reproducao.
- Para AWS real, resolver explicitamente `profile`, `account_id` e `region`
  antes da coleta.
- `region` e obrigatoria para servicos regionais. Nao inferir varredura global.
- `--output-dir` deve apontar para diretorio existente, ou a execucao deve
  receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario precisa iniciar uma analise arquitetural a partir de uma conta ou
  fixture AWS;
- uma capability downstream precisa de `inventory.json`;
- o escopo de coleta esta limitado a uma regiao ou a uma fixture.

Nao execute quando:

- o pedido implicar alteracao de recurso AWS;
- o usuario pedir varredura de todas as regioes sem justificar escopo;
- credenciais, profile ou region estiverem ambiguos em execucao real;
- o objetivo for auditoria de seguranca detalhada, caso em que o agente
  `aws-security-governance-auditor` e mais especifico.

## Regras de coleta

1. Usar apenas comandos AWS read-only declarados na allowlist do repository.
2. Registrar no `collection-metadata.json` se a fonte foi fixture ou AWS real.
3. Registrar `account_id`, `region`, `profile`, quantidade de recursos e lacunas.
4. Normalizar recursos no schema comum antes de gerar artefatos.
5. Preservar lacunas de coleta em `inventory.json`; nao converter lacuna em
   "sem risco".
6. Nao imprimir valores de credenciais, variaveis sensiveis ou payloads brutos
   extensos em saidas humanas.

## Criterios de qualidade

- `inventory.json` contem `account_id`, `region`, `resources`, `resource_count`,
  `services` e `gaps`.
- `inventory-summary.md` separa escopo, servicos e lacunas.
- `collection-metadata.json` permite reproduzir a coleta sem expor segredo.
- Falhas parciais viram lacunas documentadas quando a coleta principal ainda e
  util; falhas de escopo param a execucao.

## Escalacao

Pedir confirmacao humana antes de prosseguir se:

- a analise precisar cobrir producao sem profile/conta explicitamente
  informados;
- houver pedido para coletar multiplas regioes;
- a coleta retornar dados potencialmente sensiveis demais para relatorio humano.
