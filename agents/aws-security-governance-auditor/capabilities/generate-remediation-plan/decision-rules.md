# Decision Rules: Generate Remediation Plan

## Objetivo de decisao

Gerar plano manual de remediacao a partir de findings consolidados, sem aplicar
mudancas em AWS.

## Entradas minimas

- `--audit-dir` deve existir.
- O diretorio deve conter findings de auditoria em JSON.
- `--output-dir` deve existir ou receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario precisa priorizar correcoes;
- findings ja foram revisados ou consolidados;
- a saida esperada e roteiro manual/revisavel.

Nao execute quando:

- o usuario quer que o agente altere recursos;
- findings estao incompletos ou sem evidencia;
- a remediacao exige decisao de negocio ainda nao tomada.

## Regras de planejamento

1. Plano nunca executa correcoes; `execution` deve ser `unsupported`.
2. Agrupar por severidade em ordem de risco.
3. Cada item deve apontar recurso, acao proposta e validacao read-only posterior.
4. Nao incluir comandos mutaveis prontos para copiar sem revisao.
5. Nao prometer rollback automatico.
6. Reexecutar auditoria read-only deve ser o criterio de validacao.

## Criterios de qualidade

- `remediation-plan.md` existe e declara que nao executa correcoes.
- Itens criticos/high aparecem antes dos demais.
- Cada acao proposta deriva de finding com evidencia.
- O plano nao contem segredo, policy crua ou payload sensivel.

## Escalacao

Pedir aprovacao humana para remediacoes que possam afetar acesso, producao,
clientes, auditoria regulatoria ou contas compartilhadas.
