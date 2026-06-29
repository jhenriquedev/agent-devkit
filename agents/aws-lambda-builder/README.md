# AWS Lambda Builder

Agente especialista para gerar projetos AWS Lambda seguros e revisaveis, com
handler, fixture de evento, testes locais, template SAM, revisao de seguranca,
empacotamento local e plano de deploy sem aplicar mudancas na AWS.

## Capabilities

- `plan-lambda`: planeja Lambda sem escrever arquivos.
- `generate-lambda-project`: planeja ou escreve projeto Lambda local.
- `review-lambda-security`: revisa IAM, secrets, env vars e configuracao.
- `package-lambda`: empacota projeto local em zip sem publicar.
- `deploy-lambda-plan`: gera plano de deploy sem executar.

## Exemplo

```bash
./agent --json run aws-lambda-builder plan-lambda --spec lambda-spec.yaml
```

Deploy real nao e executado por este agente.
