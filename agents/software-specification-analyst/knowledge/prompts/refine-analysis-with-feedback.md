# Prompt: Refine Analysis With Feedback

## OBJETIVO
Incorporar respostas do stakeholder, correções e revisões aos documentos de
análise existentes, produzindo análise refinada, perguntas resolvidas,
perguntas remanescentes e registro de decisões, com rastreabilidade completa.

## ENTRADAS
- `analysis_dir`: pasta com documentos de análise existentes. Obrigatório.
- `feedback`: texto ou arquivo com respostas/correções do stakeholder. Obrigatório.
- `strictness`: `lenient` | `standard` | `strict` (default `standard`).

## PASSOS DE RACIOCÍNIO
1. Leia os documentos de análise existentes (especialmente `business-questions.md`,
   `open-decisions.md`, `critical-points.md`).
2. Leia o feedback e identifique:
   - Respostas a perguntas abertas (quais perguntas foram respondidas?).
   - Correções de inferências ou fatos incorretos.
   - Novas informações que abrem novos pontos.
   - Decisões tomadas explicitamente pelo stakeholder.
3. Para cada item do feedback:
   - Marque a pergunta como `RESPONDIDA` e registre a resposta com data.
   - Promova `INFERÊNCIA` a `FATO CONFIRMADO` quando o feedback confirmar.
   - Corrija `FATO OBSERVADO` incorreto e registre a correção.
   - Abra nova pergunta se o feedback revelar nova lacuna.
4. Verifique novamente a rubrica de suficiência
   (`analysis_policy.sufficient_context_criteria` em `policies.yaml`).
5. Produza veredito atualizado: `PRONTO PARA SPEC FINAL` ou `REQUER MAIS INPUT`.

## FORMATO DE SAÍDA (4 artefatos)
- **refined-analysis.md**: análise atualizada com fatos confirmados, decisões
  incorporadas, inferências restantes e novo veredito de suficiência.
- **resolved-questions.md**: tabela `Pergunta | Resposta | Data | Fonte`.
- **remaining-open-questions.md**: perguntas ainda não respondidas, classificadas
  por criticidade (bloqueante/importante/nice-to-have).
- **decision-log.md**: registro de decisões `Decisão | Fonte | Data | Impacto`.

## NÃO FAÇA
- Não altere fato confirmado sem registrar a correção no decision-log.
- Não feche pergunta bloqueante sem resposta explícita.
- Não promova inferência a fato confirmado sem evidência no feedback.
