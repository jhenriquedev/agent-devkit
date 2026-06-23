# Prompt — analyze-product-context

## OBJETIVO
Analisar requisitos, jornadas de usuario e riscos de produto antes de iniciar o design.

## ENTRADAS
- `--source`: documentos de requisitos, especificacoes, jornadas, epics, user stories.
- `--brief`: descricao do produto.
- `--platform`: web | mobile | both.

## RACIOCINIO (passos)
1. Consolide todas as fontes; aplique `depth-scope-rules.md` para classificar profundidade e escopo.
2. Extraia: objetivo central do produto, personas principais, jornadas criticas, fluxos de dados ou permissoes relevantes.
3. Identifique riscos de UX: fluxos complexos, estados ausentes, regras de negocio incertas, inconsistencias entre fontes.
4. Mapeie telas e areas inferidas a partir dos requisitos; cite SRC-xxx para cada uma.
5. Gere perguntas priorizadas para o que nao pode ser decidido sem confirmacao.

## REGRAS DE DECISAO
- Requisito ambiguo → registre em open-design-questions.md com rotulo "Risco: decisao necessaria".
- Plataforma nao definida → pergunte antes de sugerir navegacao ou breakpoints.
- Conflito entre fontes → registre o conflito e as opcoes; nao decida sem stakeholder.

## SAIDA
- `design-brief.md`: objetivo, personas, plataforma, escopo, restricoes.
- `screen-inventory.md`: telas e areas mapeadas com fonte.
- `source-traceability.md`: rastreabilidade de requisito → tela/fluxo.
- `open-design-questions.md`: riscos e perguntas priorizadas.

## NAO FACA
- Nao decida regra de negocio ambigua; registre como pergunta.
- Nao produza wireframes detalhados sem ter profundidade classificada.
