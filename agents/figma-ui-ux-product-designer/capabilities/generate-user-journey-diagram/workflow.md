# Prompt — generate-user-journey-diagram

## OBJETIVO
Gerar diagrama de jornada do usuario a partir de brief, card ou entrevista.

## ENTRADAS
- `--brief`: descricao do fluxo/produto.
- `--source`: documentos, cards, requisitos.
- `--platform`: web | mobile | both.

## RACIOCINIO (passos)
1. Identifique: ator principal, gatilho de inicio, objetivo final.
2. Mapeie os passos principais do fluxo; identifique pontos de decisao (sim/nao, sucesso/erro).
3. Para cada passo: registre o estado de UI correspondente (ex.: loading, form, confirmacao).
4. Inclua caminhos de erro e recuperacao.
5. Decida o modo de saida:
   - `plan_only`: gere Mermaid no `journey-diagram.md`.
   - `direct_mcp` (quando `generate-diagram.yaml` estiver em `FIGMA_EXECUTION_OPERATIONS`): acione bridge com `generate_diagram` para criar FigJam.
6. Registre lacunas de negocio em open-design-questions.md.

## REGRAS DE DECISAO
- Lacuna de regra de negocio no fluxo → registre em perguntas abertas antes de fechar o diagrama.
- Se o bridge nao estiver disponivel, entregue Mermaid local (nao e uma falha).

## SAIDA
- `journey-diagram.md`: diagrama Mermaid ou referencia ao FigJam criado.
- `open-design-questions.md`: lacunas identificadas.

## NAO FACA
- Nao invente estados intermediarios sem fonte; rotule como "A confirmar".
- Nao afirme criacao FigJam sem evidencia do bridge.
