# Prompt: Create Analysis Dossier

## OBJETIVO
Consolidar todos os documentos intermediários de análise em um dossiê único,
revisável, que permita ao solicitante decidir se o contexto é suficiente para
gerar a especificação final.

## ENTRADAS
- `input`: pasta com documentos intermediários ou texto consolidado. Obrigatório.
- Documentos esperados: discovery notes, analysis context, business rules,
  critical points, business questions, open decisions (produzidos por
  `analyze-project-context`, `identify-*`, `create-discovery-notes`).

## PASSOS DE RACIOCÍNIO
1. Leia todos os documentos intermediários disponíveis.
2. Consolide sem duplicar: unifique perguntas repetidas, classifique riscos
   por impacto, agrupe decisões por dono.
3. Aplique a rubrica de suficiência de contexto
   (`analysis_policy.sufficient_context_criteria` em `policies.yaml`):
   - Problema e objetivo confirmados?
   - Atores e permissões identificados?
   - Regras de negócio confirmadas (não apenas inferidas)?
   - Nenhuma pergunta bloqueante em aberto?
   - Dados e integrações principais conhecidos?
4. Produza veredito: `PRONTO PARA SPEC FINAL` ou `REQUER MAIS INPUT` com lista
   do que falta.
5. Se `REQUER MAIS INPUT`, liste as ações específicas necessárias.

## FORMATO DE SAÍDA
- **analysis-dossier.md**: resumo executivo (profundidade, escopo, data),
  fatos confirmados, inferências remanescentes, perguntas bloqueantes (tabela),
  perguntas importantes, riscos consolidados (tabela), decisões pendentes,
  veredito de suficiência, próximos passos recomendados.

## NÃO FAÇA
- Não suprima perguntas bloqueantes para forçar veredito `PRONTO`.
- Não reescreva os documentos intermediários — consolide e referencie.
- Não gere spec nesta etapa — apenas o dossiê.
