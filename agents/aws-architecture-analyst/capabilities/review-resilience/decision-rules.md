# Decision Rules: Review Resilience

## Objetivo de decisao

Revisar sinais de resiliencia no inventario AWS e classificar achados como
confirmados, riscos potenciais ou lacunas de coleta.

## Entradas minimas

- `--inventory` deve apontar para inventario valido.
- O inventario deve conter atributos necessarios para avaliar DLQ, Multi-AZ,
  autoscaling, backups, VPC attachment e single points quando aplicavel.

## Quando executar

Execute quando:

- o usuario quer revisar disponibilidade, continuidade ou pontos unicos de
  falha;
- ha inventario de workloads suficiente para avaliar recursos principais;
- a saida esperada e recomendacao ou lacuna, nao mudanca de configuracao.

Nao execute quando:

- o usuario pede aplicar remediacao automaticamente;
- faltam recursos principais do workload e a revisao seria enganosa;
- a avaliacao depende de dados ainda nao coletados e o usuario espera conclusao
  definitiva.

## Regras de classificacao

1. Classificar `high` apenas para risco critico com evidencia concreta.
2. Classificar `medium` para risco verificavel que precisa de acao ou validacao.
3. Classificar `info` para configuracao que pode ser esperada.
4. Classificar `gap` quando atributo necessario nao foi coletado.
5. `gap` nunca significa "ok"; deve indicar atributo faltante e como coletar.
6. Para SQS, ausencia de `has_dlq` e `gap`; `has_dlq: false` e risco.
7. Para Lambda, ausencia de `vpc_attached` e `gap`; `false` e informativo salvo
   contexto de rede exigir VPC.

## Criterios de qualidade

- `resilience-findings.json` contem achados com `severity`, `message` e
  `confidence`.
- `resilience-review.md` separa risco confirmado, risco potencial e lacuna.
- Toda lacuna indica qual atributo ou collector precisa ser ampliado.
- Nenhuma recomendacao sugere alterar recurso sem plano humano posterior.

## Escalacao

Sinalizar ao humano quando:

- recurso critico aparece sem redundancia ou backup confirmados;
- dados de resiliencia estao ausentes para workload de producao;
- uma dependencia nao resolvida pode esconder single point of failure.
