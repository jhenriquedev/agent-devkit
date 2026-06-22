# Prompt: Mover Card

Objetivo: mover um work item para outro estado e, opcionalmente, outra coluna de
board, com preview de before/after e risco.

Entradas esperadas: work_item_id, project e state; board_column e reason
opcionais; --execute para escrita real.

Passos de raciocinio:

1. Leia o card e capture estado e coluna atuais.
2. Nao assuma que o estado alvo existe no processo do projeto; se incerto,
   confirme estados validos antes.
3. Classifique risco: high para fechamento como Done, Closed, Resolved ou
   Removed; medium para Active, Doing, In Progress ou Committed; low caso
   contrario.
4. Fechamento exige reason; sem reason, pare e peca.
5. Atencao a coluna: System.BoardColumn pode ser derivada do state e das regras
   do board, e nem sempre aceita escrita direta. Prefira mover por state; se
   board_column for pedido, avise o risco de a coluna nao mudar e valide depois.
6. Se nao houver mudanca real, retorne no-op. Apos confirmacao e --execute,
   aplique.

Regras de decisao:

- Sempre mostre estado/coluna atuais e alvo.
- Fechamento exige reason.
- Nao altere tags ou responsavel nesta capability.
- Nao execute escrita sem confirmacao/--execute.

Formato de saida: use templates/move-card-output.md, com Target, Before/After,
Risk, Result e Confirmation.

NAO faca: nao feche sem motivo; nao escreva sem --execute; nao infira coluna
alvo; nao trate escrita de System.BoardColumn como garantida.
