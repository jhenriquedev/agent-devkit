# Decision Rules: Audit Config Guardrails

## Objetivo de decisao

Auditar AWS Config como guardrail de governanca, verificando presenca de
configuration recorders e rules coletadas.

## Entradas minimas

- Snapshot deve conter `config.recorders` e, quando disponivel, `config.rules`.
- Em AWS real, region deve estar resolvida para AWS Config.
- `--output-dir` deve existir ou receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario quer avaliar governanca basica por AWS Config;
- ha snapshot regional de Config;
- a saida esperada e achado/recomendacao, nao habilitacao.

Nao execute quando:

- o usuario quer criar recorder/rules;
- o ambiente usa Config agregador fora do snapshot e isso nao foi coletado;
- falta region para avaliar Config regional.

## Regras de classificacao

1. Nenhum configuration recorder no snapshot e `high` confirmado.
2. Ausencia de rules pode ser lacuna ou achado futuro conforme politica
   definida; nao declarar compliance sem rules coletadas.
3. Evidence deve mencionar o snapshot/regiao.
4. Recomendacao deve orientar habilitar recorders e managed rules, sem executar.
5. Nao tratar ausencia de Config como ausencia de recursos fora de compliance.

## Criterios de qualidade

- `config-guardrails-audit.json` contem finding quando recorders ausentes.
- `config-guardrails-audit.md` resume evidencia e recomendacao.
- Findings usam categoria `governance`.
- Lacunas regionais ficam explicitas.

## Escalacao

Pedir revisao humana se conta de producao nao tiver recorder, se a regiao for
critica ou se a organizacao exigir Config para compliance.
