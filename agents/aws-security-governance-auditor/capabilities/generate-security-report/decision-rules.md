# Decision Rules: Generate Security Report

## Objetivo de decisao

Consolidar arquivos de auditoria em `security-findings.json` e
`security-report.md`, avaliando quality gates sem chamar AWS.

## Entradas minimas

- `--audit-dir` deve existir.
- O diretorio deve conter arquivos `*.json` de auditoria com `findings`.
- `--output-dir` deve existir ou receber `--yes-create-dir`.

## Quando executar

Execute quando:

- auditorias individuais ja foram geradas;
- o usuario precisa de visao consolidada por severidade;
- o relatorio sera usado para triagem ou governanca.

Nao execute quando:

- o usuario quer executar remediacao;
- os findings nao possuem severidade/evidencia;
- os artefatos contem segredo ou policy crua que seria propagada.

## Regras de consolidacao

1. Ignorar `security-findings.json` anterior para evitar duplicacao.
2. Consolidar todos os `findings` dos arquivos de auditoria.
3. Preservar severidade, categoria, recurso, evidencia, recomendacao e status.
4. Avaliar quality gates: allowlist, severidade, evidencia, plan-only e
   redacao de segredo.
5. Falha de quality gate deve aparecer no payload de saida.
6. Nao chamar AWS nem reexecutar auditorias.

## Criterios de qualidade

- `security-findings.json` contem contagem e findings consolidados.
- `security-report.md` resume contagens por severidade e lista findings.
- Payload stdout contem `quality_gates`.
- Relatorio nao contem secret value, access key, session token, policy crua ou
  connection string.

## Escalacao

Pedir correcao dos artefatos quando quality gate falhar, quando findings vierem
sem evidencia ou quando o relatorio for usado para aprovacao executiva.
