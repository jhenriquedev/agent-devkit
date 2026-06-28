# Decision Rules: Generate Operation Report

## Objetivo de decisao

Gerar relatorio read-only a partir dos artefatos de uma operacao planejada ou
executada, sem chamar AWS e sem reexecutar mutacoes.

## Entradas minimas

- `--operation-dir` deve existir.
- `operation-dry-run.json` deve existir no diretorio informado.
- `operation-result.json` e opcional e indica execucao real.

## Quando executar

Execute quando:

- o usuario precisa consolidar evidencia de uma operacao;
- os artefatos foram gerados por capabilities deste agente;
- a saida esperada e `operation-report.md`.

Nao execute quando:

- `operation-dry-run.json` estiver ausente;
- o usuario quer executar ou repetir a operacao;
- os artefatos contem payload bruto ou segredo que nao deve ser propagado.

## Regras de decisao

1. Esta capability nunca chama AWS.
2. Ausencia de `operation-result.json` significa operacao planejada, nao
   executada.
3. Relatorio deve preservar status, recurso, ambiente, region e profile.
4. Preflight, post-check e account validation podem ser incluados se ja existirem
   nos artefatos.
5. Payload bruto ou segredo deve ser omitido; usar apenas hash/tamanho ja
   presente.
6. Nao transformar dry-run em evidencia de execucao.

## Criterios de qualidade

- `operation-report.md` existe no output.
- O campo `Executed` reflete a presenca de resultado executado.
- Relatorio diferencia plano, execucao, preflight e post-check.
- O arquivo nao contem payload sensivel bruto.

## Escalacao

Pedir revisao humana se os artefatos estiverem incompletos, vierem de diretorio
desconhecido ou forem usados como evidencia de mudanca em producao.
