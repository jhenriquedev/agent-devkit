# Decision Rules: Audit S3 Buckets

## Objetivo de decisao

Auditar buckets S3 quanto a Public Access Block e encryption detectavel, usando
metadados read-only.

## Entradas minimas

- Snapshot deve conter `s3.buckets`.
- Cada bucket deve ter, quando coletado, `PublicAccessBlock` e `Encryption`.
- `--output-dir` deve existir ou receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario quer revisar exposicao e encryption de buckets;
- ha snapshot S3 ou acesso read-only para coletar metadados;
- o objetivo e finding/recomendacao, nao remediacao.

Nao execute quando:

- o usuario quer alterar bucket policy, ACL, PAB ou encryption;
- a auditoria depende de policy completa que nao foi coletada;
- o bucket e publico intencionalmente e falta contexto de negocio.

## Regras de classificacao

1. Qualquer flag de Public Access Block ausente ou falsa e `high`.
2. Encryption ausente ou nao detectada e `medium` com `status: potential`.
3. Ausencia de metadado de encryption e risco potencial, nao prova de dado sem
   encryption.
4. Nao imprimir bucket policy ou ACL crua em Markdown.
5. Bucket desconhecido deve ser reportado como `unknown-bucket`.

## Criterios de qualidade

- `s3-buckets-audit.json` contem findings de `public-exposure` e `encryption`.
- `s3-buckets-audit.md` resume evidencia e recomendacao sem policy crua.
- Findings distinguem confirmado de potencial.
- Lacunas de PAB/encryption ficam visiveis para nova coleta.

## Escalacao

Pedir revisao humana para bucket de producao, dado sensivel, PAB incompleto ou
encryption ausente em ambiente regulado.
