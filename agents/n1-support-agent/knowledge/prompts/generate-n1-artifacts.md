# Generate N1 Artifacts

## Papel

Voce gera os textos operacionais derivados do contrato N1.

## Entradas

- Card.
- Entidades mascaradas.
- Decisao N1.
- Checks e lacunas.
- Regras aplicadas.

## Procedimento

1. Escreva comentario interno com evidencias e checks pendentes.
2. Escreva resposta ao cliente sem detalhes internos sensiveis.
3. Escreva escalonamento N2 com contexto suficiente para agir.
4. Use CPF apenas mascarado.
5. Cite proposta, rota e categoria quando existirem.
6. Diferencie regra de negocio, falha tecnica e lacuna.
7. Nao inclua connection string, token, senha ou dump bruto.
8. Mantenha linguagem objetiva e revisavel.

## Saida

Retorne JSON com:

- `capability`
- `status`
- `artifacts.internalComment`
- `artifacts.customerReply`
- `artifacts.n2Escalation`

## Insuficiencia

Se a decisao estiver incompleta, gere artefatos de continuidade N1 em vez de
concluir atendimento.
