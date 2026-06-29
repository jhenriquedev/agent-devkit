# AWS Lambda Builder

Instrucoes locais para trabalhar no agente `aws-lambda-builder`.

## Responsabilidade

Este agente planeja, gera, revisa, empacota localmente e cria planos de deploy
para projetos AWS Lambda. Ele produz artefatos revisaveis e nao executa deploy
real.

## Fora De Escopo

- Invocar Lambdas existentes: pertence ao `aws-operations-operator`.
- Deploy real ou mutacao AWS.
- Criar conta AWS, roles reais ou infraestrutura completa.
- Instalar dependencias automaticamente.
- Suporte completo a todos os runtimes ou CDK completo.

## Guardrails

- Deploy real e sempre fora da primeira fase.
- Nunca chamar `aws`, `sam deploy`, `serverless deploy` ou `cdk deploy`.
- Bloquear segredos hardcoded.
- Bloquear IAM wildcard sem justificativa.
- Gerar testes locais e fixtures de evento.
- Empacotamento local deve ser dry-run por padrao.
- Escrita local deve ficar dentro de `target_project`.
