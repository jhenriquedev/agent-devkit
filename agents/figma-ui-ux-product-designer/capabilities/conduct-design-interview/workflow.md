# Prompt — conduct-design-interview

## OBJETIVO
Levantar contexto suficiente para desenhar sem inventar regra de negocio.

## ENTRADAS
- `--brief`: descricao textual do projeto/demanda.
- `--source`: arquivos ou pastas com material de referencia.
- `--platform`: web | mobile | both.
- `--target-audience`: descricao do publico-alvo.
- `--design-style`: preferencias visuais ou referencia de marca.

## RACIOCINIO (passos)
1. Leia brief e fontes; aplique `depth-scope-rules.md` para classificar profundidade (light/medium/deep) e escopo (tela/fluxo/modulo/produto).
2. Identifique o que JA esta sustentado nas fontes versus o que esta ausente ou ambiguo.
3. Gere perguntas separadas por categoria:
   - **Objetivo do usuario:** qual problema o produto resolve; qual e o sucesso do usuario.
   - **Personas:** quem usa, nivel tecnico, necessidades especiais de acessibilidade.
   - **Regras de negocio nao inferiveis:** permissoes, limites, criterios de aceite opacos.
   - **Design system existente:** ha guia de estilo, tokens, componentes versionados?
   - **Estados obrigatorios:** quais telas precisam de estado vazio/loading/erro/sucesso?
   - **Plataforma e guidelines:** iOS/Material/web responsivo/identidade propria?
   - **Criterio de aprovacao:** quem aprova, quais sao os gates de entrega?
4. Ordene perguntas por impacto: perguntas sem resposta que bloqueiam decisao de design primeiro.

## REGRAS DE DECISAO
- Nunca assuma regra de negocio ambigua → vira pergunta em open-design-questions.md.
- Se houver menos de 2 fontes substanciais, priorize entrevista (depth=light) antes de prosseguir para design.
- Se o brief nao definir plataforma, pergunte antes de propor telas.

## SAIDA
- `design-brief.md`: objetivo, publico, plataforma, escopo, fontes.
- `open-design-questions.md`: perguntas por categoria.
- `source-traceability.md`: mapa de fonte → informacao extraida.

## NAO FACA
- Nao proponha telas finais antes de fechar objetivo e publico.
- Nao afirme ter compreendido regra de negocio sem fonte que a sustente.
