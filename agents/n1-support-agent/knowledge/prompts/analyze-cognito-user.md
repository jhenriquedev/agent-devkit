# Analyze Cognito User

## Papel

Voce verifica se existe evidencia disponivel sobre o usuario Cognito do cliente.

## Entradas

- CPF mascaravel ou CPF bruto recebido como argumento.
- E-mail ou telefone quando presentes.
- Contexto do card e rota de sintoma.
- Estado das integracoes disponiveis no agente.

## Procedimento

1. Normalize e masque CPF antes de responder.
2. Verifique se existe repository, agente ou capability Cognito configurado.
3. Se a ferramenta existir, consulte apenas leitura.
4. Se a ferramenta nao existir, nao simule status ativo, bloqueado ou ausente.
5. Registre lacuna diagnostica apontando fonte `cognito`.
6. Explique que status de enablement nao foi verificado automaticamente.
7. Preserve e-mail e telefone como flags booleanas, nao como dump de PII.

## Saida

Retorne JSON com:

- `capability`
- `status`
- `checkStatus`
- `reason`
- `facts.cpfMasked`
- `facts.emailProvided`
- `facts.phoneProvided`
- `diagnosticGaps`
- `errors`

## Insuficiencia

Quando Cognito nao estiver integrado, use `checkStatus=unavailable`. Nunca
classifique o problema como resolvido por falta de consulta.
