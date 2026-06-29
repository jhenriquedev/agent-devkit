# Decision Rules

- Nunca executar deploy real.
- Nao chamar AWS CLI, SAM, Serverless ou CDK.
- Plano deve listar pre-requisitos, IAM, env vars e rollback.
- Deploy real pertence a capability futura com `write_policy: confirm`.
