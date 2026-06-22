# Generate Patch Plan

## Objetivo

Gerar `patch_plan.md` completo, seguro e pronto para implementacao quando o gate
permitir.

## Entradas

- Contexto N2.
- Analise de codigo.
- Causa raiz.
- Destino `--output` ou card Azure.

## Raciocinio

1. Monte contexto e diagnostico.
2. Liste evidencias, contradicoes e lacunas.
3. Defina escopo dentro e fora.
4. Gere estrategia TDD.
5. Liste atividades de reproducao, correcao, migration e observabilidade.
6. Gere comandos de validacao e criterios de aceite.
7. Calcule readiness com destino, fonte, codigo e confianca.

## Rubrica/Regras

- Plano pronto exige destino, card ou N1, arquivo candidato e confianca >= 0.65.
- Categoria `insufficient_evidence` bloqueia readiness.
- Saida humana mascara CPF e e-mail.

## Saida

Markdown `patch_plan.md` e contrato JSON com `patchPlan`, `rootCause` e
`codeAnalysis`.

## Nao faca

- Nao implementar patch.
- Nao inventar arquivos inexistentes.
- Nao ocultar perguntas bloqueantes.
