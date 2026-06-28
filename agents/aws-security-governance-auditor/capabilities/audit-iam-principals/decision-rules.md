# Decision Rules: Audit IAM Principals

## Objetivo de decisao

Auditar principals e policies IAM em modo read-only, identificando permissao
wildcard e risco de privilegio excessivo sem expor policy completa em relatorio
humano.

## Entradas minimas

- Usar `--fixture` em testes ou revisoes locais.
- Em AWS real, profile/credenciais devem resolver via cadeia padrao da AWS.
- `--output-dir` deve existir, ou a execucao deve receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario quer revisar risco de IAM em conta AWS;
- ha snapshot de IAM ou permissao read-only para coletar policies;
- a saida esperada e achado com evidencia, nao correcao.

Nao execute quando:

- o pedido envolver anexar/remover policy, criar usuario ou alterar role;
- o usuario quiser imprimir policy completa em Markdown;
- a coleta de documentos de policy falhar e a conclusao depender deles.

## Regras de classificacao

1. `Allow Action=* Resource=*` e `critical` confirmado.
2. Permissoes amplas por servico sem condicao devem ser tratadas como `high`
   quando implementadas por auditor futuro.
3. Ausencia de documento de policy e lacuna de coleta, nao ausencia de risco.
4. Evidencia humana deve resumir a condicao perigosa, nao copiar policy crua.
5. Principal desconhecido deve ser identificado como `unknown`, sem inventar
   owner ou criticidade.

## Criterios de qualidade

- `iam-audit.json` contem findings com campos obrigatorios de `policies.yaml`.
- `iam-audit.md` redige policies completas e segredos.
- Todo finding tem severidade valida, evidencia e recomendacao.
- Lacunas de coleta ficam explicitas para nova execucao.

## Escalacao

Sinalizar ao humano quando houver wildcard admin confirmado, uso em producao ou
policy critica sem owner claro.
