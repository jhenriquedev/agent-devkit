# N2 Support Agent

Agente N2 para investigacao tecnico-operacional, analise de causa raiz e
geracao de `patch_plan.md` pronto para desenvolvimento.

## Objetivo

Receber contexto de sustentacao ja triado ou um card Azure DevOps, analisar
evidencias e codigo relacionado, classificar a causa raiz e entregar um plano de
patch seguro, testavel e ordenado para um dev ou outro agente executar.

## Uso

```bash
./ai-devkit run n2-support-agent execute-n2-investigation --project "Sustentacao" --card 8801 --codebase-path ~/jhss/dev/meucashcard/mcc_lambda --output /tmp/patch_plan.md --format json
./ai-devkit run n2-support-agent generate-patch-plan --codebase-path ~/jhss/dev/meucashcard/mcc_lambda --output /tmp/patch_plan.md
./ai-devkit run n2-support-agent validate-n1-handoff --n1-contract /tmp/n1.json --format json
./ai-devkit run n2-support-agent select-specialist-checks --n1-contract /tmp/n1.json --codebase-path ~/jhss/dev/meucashcard/mcc_lambda --format json
./ai-devkit run n2-support-agent review-patch-plan-readiness --project "Sustentacao" --card 8801 --codebase-path ~/jhss/dev/meucashcard/mcc_lambda --format json
```

Sem `--execute`, atualizacoes no Azure ficam planejadas. Com `--execute`, o
agente pode solicitar comentario, tags, movimentacao e anexo do `patch_plan.md`
ao `azure-devops-orchestrator`.

## Responsabilidade

O N2 nao refaz o N1. Ele valida o handoff, investiga causa raiz, cruza codigo e
evidencias, define plano de correcao e documenta o card.

## Capabilities de efetividade

- `validate-n1-handoff`: valida se o contrato N1 e suficiente.
- `select-specialist-checks`: escolhe BPO, banco, logs ou N1 conforme hipotese.
- `execute-specialist-validation`: estrutura validacoes especialistas.
- `rank-code-findings`: ranqueia codigo priorizando source sobre testes.
- `build-reproduction-strategy`: gera estrategia TDD de reproducao.
- `review-patch-plan-readiness`: bloqueia plano com lacunas.
- `update-n2-card-workflow`: prepara a esteira Azure do N2 com alvo explicito.

Saidas humanas devem mascarar CPF e e-mail. Capabilities auxiliares que recebem
`--output` escrevem apenas seu proprio artefato, sem gerar `patch_plan.md` por
efeito colateral.
