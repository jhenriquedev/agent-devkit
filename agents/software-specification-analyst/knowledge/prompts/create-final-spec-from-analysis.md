# Prompt: Create Final Spec From Analysis

## OBJETIVO
Gerar o pacote de especificação completa (7 artefatos, 21 seções) a partir de
documentos de análise refinados e maduros, preservando rastreabilidade e
explicitando pendências remanescentes.

## PRÉ-CONDIÇÃO OBRIGATÓRIA
Aplique a rubrica de suficiência de contexto ANTES de gerar qualquer artefato
(`analysis_policy.sufficient_context_criteria` em `policies.yaml`):
1. Problema e objetivo confirmados pelo stakeholder?
2. Atores e permissões identificados (não "a definir")?
3. Regras de negócio confirmadas (não apenas inferidas do código)?
4. Nenhuma pergunta bloqueante em aberto?
5. Dados e integrações principais conhecidos?

Se algum critério falhar, PARE: entregue análise refinada + lista do que falta
e explique por que a spec final não pode ser gerada agora.

## ENTRADAS
- `analysis_dir`: pasta com documentos refinados. Obrigatório.
- `title`: título da spec (opcional; inferido dos documentos se ausente).

## PASSOS DE RACIOCÍNIO
1. Verifique a rubrica de suficiência (ver pré-condição).
2. Leia todos os `.md` de `analysis_dir` — use fatos confirmados como base.
3. Para cada uma das 21 seções de `specification_policy.required_sections`,
   preencha com fatos confirmados da análise. Onde não houver evidência, escreva
   `Pergunta Aberta: [descrição da lacuna]` — nunca "A definir" mudo.
4. Numere RF/RNF; separe regras de negócio; gere user stories com CA; modele
   jornadas em Mermaid; monte a matriz de rastreabilidade.
5. Rode os `quality_gates` de `policies.yaml`; liste os que não passaram.
6. Encerre com `## Handoff Para Desenvolvimento` contendo: lista de artefatos,
   pendências bloqueantes, próximo passo recomendado.

## FORMATO DE SAÍDA (7 artefatos)
- **software-specification.md**: as 21 seções, terminando em
  `## Handoff Para Desenvolvimento`.
- **functional-spec.md**: spec funcional detalhada.
- **technical-spec.md**: spec técnica com arquitetura, dados, APIs, segurança.
- **user-stories.md**: épicos, features, histórias com CA (Gherkin quando
  há fluxo condicional).
- **journey-flows.md**: jornadas e fluxogramas Mermaid.
- **requirements-traceability.md**: matriz RF/RNF ↔ US ↔ CA ↔ componente ↔ teste.
- **open-questions.md**: perguntas remanescentes classificadas por criticidade.

## NÃO FAÇA
- Não omita a seção `## Handoff Para Desenvolvimento`.
- Não promova sugestão técnica a requisito de produto.
- Não feche decisão de produto sem confirmação explícita na análise.
- Não gere spec se a rubrica de suficiência falhar — entregue análise.
