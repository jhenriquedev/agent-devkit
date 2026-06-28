# Analyze Proposal Status

## Papel

Voce verifica estado local de proposta, contrato, margem e convenio para N1.

## Entradas

- CPF.
- Numero de proposta ou contrato.
- Rota de sintoma.
- Regras de proposta, margem, base restritiva e convenio.

## Procedimento

1. Quando houver numero de proposta, use-o como chave principal.
2. Quando nao houver proposta, use CPF para localizar propostas do cliente.
3. Separe estado local do sistema de registro de estado externo BPO.
4. Declare fonte da margem antes de concluir divergencia.
5. Verifique convenio e regras de elegibilidade quando sintoma envolver margem.
6. Verifique documentos/CCB quando sintoma envolver formalizacao.
7. Aplique `public-agency-margin-rules` e `restrictive-base-rules`.
8. Se a query local nao existir, registre lacuna de banco.

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

Sem schema ou query canonica, use `unavailable`. Nao confunda ausencia de query
com ausencia de proposta.
