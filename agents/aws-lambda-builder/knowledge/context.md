# Contexto

O projeto ja possui agentes AWS para analise, auditoria e operacoes. Este agente
nao substitui essas responsabilidades:

- `aws-operations-operator` opera recursos existentes com confirmacao.
- `aws-security-governance-auditor` audita recursos existentes.
- `aws-architecture-analyst` analisa workloads existentes.

O `aws-lambda-builder` cria artefatos locais para novas Lambdas e planos de
deploy revisaveis. Deploy real deve ser implementado futuramente como capability
separada com `write_policy: confirm`.
