# Decision Rules: Audit Encryption

## Objetivo de decisao

Auditar sinais de encryption detectavel, atualmente a partir dos findings de S3
e demais metadados coletados no snapshot quando disponiveis.

## Entradas minimas

- Snapshot deve conter dominios com metadados de encryption, especialmente
  `s3.buckets`.
- `--output-dir` deve existir ou receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario quer revisar encryption em recursos coletados;
- ha metadados suficientes para indicar ausencia ou lacuna;
- o objetivo e finding e recomendacao manual.

Nao execute quando:

- o usuario quer habilitar encryption;
- a fonte nao coletou encryption e o usuario espera atestado de conformidade;
- o recurso exige auditoria de KMS profunda ainda nao implementada.

## Regras de classificacao

1. S3 sem encryption detectada e `medium` com `status: potential`.
2. Ausencia de metadado nao prova ausencia de encryption; indicar potencial ou
   lacuna conforme snapshot.
3. Nao expor KMS policy completa ou material sensivel.
4. Nao declarar compliance sem metadados suficientes.
5. Findings devem recomendar SSE-S3 ou KMS conforme contexto, sem executar.

## Criterios de qualidade

- `encryption-audit.json` contem somente findings de categoria `encryption`.
- `encryption-audit.md` separa evidencia de recomendacao.
- Findings usam severidade valida e evidencia nao vazia.
- Remediacao permanece manual/planejada.

## Escalacao

Pedir coleta adicional quando recursos criticos nao trazem metadados de
encryption, especialmente storage de producao ou dados regulados.
