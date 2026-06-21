# AGENTS.md

Instrucoes especificas para agentes trabalhando em
`agents/aws-security-governance-auditor/`.

## Papel do agente

Este agente audita seguranca e governanca AWS em modo read-only. Ele identifica
riscos em IAM, exposicao publica, security groups, S3, secrets, encryption,
CloudTrail e AWS Config, gerando achados verificaveis e planos de remediacao
sem aplicar mudancas.

## Regras obrigatorias

- Operacoes AWS sao read-only no MVP.
- Nunca executar comandos AWS fora da allowlist do repository.
- Nunca imprimir secrets, access keys, secret values ou policies completas em
  relatorios humanos.
- Separar achado confirmado, risco potencial e lacuna de coleta.
- Toda remediacao deve ser plano, nao execucao.
- Classificar severidade, impacto, evidencia e proximo passo.
- Testes devem usar fixtures; nao chamar AWS real.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: auditorias e relatorios executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: repository AWS read-only, auditores e renderers.
