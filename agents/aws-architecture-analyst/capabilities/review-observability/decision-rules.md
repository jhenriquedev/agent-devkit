# Decision Rules: Review Observability

## Objetivo de decisao

Avaliar sinais operacionais no inventario AWS, incluindo CloudWatch alarms, log
groups, retencao e lacunas de telemetria.

## Entradas minimas

- `--inventory` deve apontar para inventario valido.
- O inventario deve conter recursos de workload e, quando disponivel, alarms e
  log groups.

## Quando executar

Execute quando:

- o usuario quer saber se workloads inventariados possuem sinais minimos de
  observabilidade;
- ha inventario local e a saida esperada e relatorio;
- a analise pode ser feita sem consultar logs brutos.

Nao execute quando:

- o usuario precisa buscar eventos ou erros em logs, caso em que
  `aws-cloudwatch-log-analyzer` e mais especifico;
- o pedido exige criar alarms, dashboards ou log groups;
- a ausencia de alarms/logs pode ser explicada por escopo de coleta incompleto e
  isso nao estiver declarado.

## Regras de classificacao

1. Nenhum CloudWatch alarm no inventario e `medium`, salvo se o escopo declarou
   que alarms nao foram coletados; nesse caso e `gap`.
2. Log group sem retencao coletada e `gap`, nao conformidade assumida.
3. Log group com retencao ausente ou infinita pode ser `info` ou `medium`
   conforme criticidade declarada.
4. Nao tratar ausencia de logs como ausencia de problema operacional.
5. Nao expor payloads de logs; esta capability avalia metadados, nao conteudo.

## Criterios de qualidade

- `observability-findings.json` lista achados com severidade e confianca.
- `observability-review.md` separa sinais presentes, lacunas e perguntas.
- Recomendacoes indicam proximos passos de coleta ou revisao, sem criar recurso.
- Findings evitam conclusoes absolutas quando CloudWatch nao foi completamente
  inventariado.

## Escalacao

Pedir contexto humano quando:

- workload e critico mas nao ha alarms ou logs;
- o usuario espera diagnostico de incidente, nao revisao arquitetural;
- a retencao de logs pode envolver requisito regulatorio.
