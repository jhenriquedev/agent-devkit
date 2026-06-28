# Decision Rules: Audit CloudTrail Config

## Objetivo de decisao

Auditar presenca de CloudTrail na conta/regiao coletada e sinalizar ausencia de
trails como risco critico de governanca.

## Entradas minimas

- Snapshot deve conter `cloudtrail.trails`.
- Em AWS real, region deve estar resolvida quando a coleta regional for
  necessaria.
- `--output-dir` deve existir ou receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario quer verificar trilha de auditoria AWS;
- ha snapshot CloudTrail ou permissao read-only para `describe-trails`;
- a saida sera usada como achado ou lacuna.

Nao execute quando:

- o usuario quer criar trail, bucket ou log validation;
- a organizacao usa CloudTrail org-level fora do escopo e isso nao foi coletado;
- falta region/snapshot e a conclusao seria incompleta.

## Regras de classificacao

1. Nenhum trail presente no snapshot e `critical` confirmado para o escopo
   coletado.
2. Trail presente sem status detalhado deve gerar pergunta/lacuna futura, nao
   atestado completo.
3. Nao assumir que CloudTrail organizacional existe sem evidencia.
4. Evidence deve mencionar ausencia no snapshot, nao ausencia absoluta global.
5. Recomendacao deve orientar habilitar CloudTrail centralizado e validacao de
   logs, sem executar.

## Criterios de qualidade

- `cloudtrail-audit.json` contem finding critico quando nao ha trails.
- `cloudtrail-audit.md` mostra escopo e evidencia.
- Resultado separa ausencia confirmada no snapshot de lacunas de coleta.
- Nenhum comando mutavel e sugerido como aplicado.

## Escalacao

Sinalizar ao humano quando conta de producao nao tiver trail detectado ou quando
a coleta nao cobrir organizacao/region necessaria.
