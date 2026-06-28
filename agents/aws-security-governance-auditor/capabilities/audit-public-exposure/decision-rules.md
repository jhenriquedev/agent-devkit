# Decision Rules: Audit Public Exposure

## Objetivo de decisao

Auditar exposicao publica combinando findings de Security Groups e S3, sem
alterar recursos e sem assumir que ausencia de dado significa seguro.

## Entradas minimas

- Snapshot deve conter `security_groups` e/ou `s3.buckets`.
- Para AWS real, `region` e necessaria para Security Groups.
- `--output-dir` deve existir ou receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario quer revisar superfícies publicas em rede e storage;
- ha snapshot com Security Groups ou buckets S3;
- a saida precisa consolidar exposicoes de diferentes dominios.

Nao execute quando:

- o usuario quer aplicar bloqueio de acesso publico ou editar SG;
- o foco e apenas rede profunda, onde `audit-security-groups` e mais direto;
- faltam os dominios coletados e a conclusao seria enganosa.

## Regras de classificacao

1. Ingress `0.0.0.0/0` ou `::/0` em 22/3389 e `critical`.
2. Ingress publico em outras portas e `high`, salvo contexto futuro mais
   especifico.
3. S3 Public Access Block incompleto e `high`.
4. Exposicao publica + dado sensivel deve elevar severidade quando evidenciado.
5. Dado nao coletado e lacuna, nao finding seguro.

## Criterios de qualidade

- `public-exposure.json` agrega findings de SG e S3 publicos.
- `public-exposure.md` mostra recurso, severidade, evidencia e recomendacao.
- Findings mantem `status` como `confirmed` quando a evidencia veio do snapshot.
- Nao incluir ACL/policy crua de bucket em Markdown.

## Escalacao

Pedir revisao humana imediata para SSH/RDP aberto ao mundo, bucket sensivel com
PAB incompleto ou exposicao em conta de producao.
