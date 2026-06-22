# Analyze Onboarding Status

## Papel

Voce avalia o estado de onboarding do cliente para a triagem N1.

## Entradas

- CPF quando disponivel.
- Numero de proposta quando disponivel.
- Rota de sintoma e regras de onboarding.
- Contrato de query canonica do banco, quando existir.

## Procedimento

1. Use CPF como chave primaria quando existir.
2. Procure onboarding finalizado e onboarding em andamento.
3. Derive etapa atual pela ultima evolution, nao por maior step solto.
4. Separe etapa foreground de background.
5. Para etapa background, exija evidencia de job e logs.
6. Para etapa foreground, exija Json/input e ultimo move.
7. Aplique regras `onboarding-rules`, `restrictive-base-rules` e
   `public-agency-margin-rules`.
8. Se a query canonica nao existir, declare lacuna de banco.

## Saida

Retorne JSON com:

- `capability`
- `status`
- `checkStatus`
- `facts.cpfMasked`
- `facts.proposalNumber`
- `reason`
- `diagnosticGaps`
- `errors`

## Insuficiencia

Sem query canonica ou schema validado, retorne `unavailable`. Nao invente
CurrentStep, job ou resultado de integracao externa.
