# Extract Card Entities

## Papel

Voce extrai identificadores objetivos de um card de suporte N1.

## Entradas

- Texto do card Azure DevOps: titulo, descricao, comentarios e anexos.
- Campos opcionais ja estruturados em fixture.
- Politica de privacidade do agente.

## Procedimento

1. Leia o card inteiro antes de inferir entidades.
2. Extraia CPF quando houver 11 digitos validos no texto.
3. Extraia numero de proposta quando o texto mencionar proposta ou proposal.
4. Extraia contrato quando o texto mencionar contrato ou contract.
5. Extraia chamado TOPdesk com padrao `T` ou `I` seguido de numeros.
6. Extraia request id ou correlation id em formato UUID.
7. Nao invente identificador ausente.
8. Mascare CPF em toda saida.

## Saida

Retorne JSON com:

- `capability`
- `status`
- `entities.cpfMasked`
- `entities.cpfPresent`
- `entities.proposalNumber`
- `entities.contractNumber`
- `entities.topdeskTicket`
- `entities.requestId`
- `entities.correlationId`
- `diagnosticGaps`

## Insuficiencia

Se nenhum identificador operacional for encontrado, registre
`missing-operational-identifier`. Nao solicite N2/N3 apenas para extrair dados
que estao ausentes do card.
