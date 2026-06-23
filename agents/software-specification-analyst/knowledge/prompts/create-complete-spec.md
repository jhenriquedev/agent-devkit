# Prompt: Create Complete Spec

## OBJETIVO
Gerar o pacote de especificação completa (7 artefatos) cobrindo as 21 seções de
`specification_policy`, a partir da demanda fornecida diretamente (sem análise
prévia de projeto).

## ENTRADAS
- `input`: arquivo Markdown/texto com a demanda. Obrigatório.
- `title`: título da especificação (opcional; inferido da demanda se ausente).

## PASSOS DE RACIOCÍNIO
1. Leia a demanda e separe explicitamente:
   - `FATO FORNECIDO` — dado explícito no input.
   - `INFERÊNCIA` — interpretação razoável.
   - `PREMISSA` — assumida para continuar.
   - `PERGUNTA ABERTA` — lacuna identificada.
2. Consulte `vendor/skills/CATALOG.md`; carregue `ecc/product-capability` e
   skills relevantes ao domínio (API, backend, frontend, segurança, testes, ML).
   Se o catálogo não existir, registre como premissa e siga sem ele.
3. Preencha as 21 seções de `specification_policy.required_sections` em
   `knowledge/policies.yaml`. Onde não houver evidência, escreva
   `Pergunta Aberta: [descrição da lacuna]` — nunca "A definir" mudo quando há
   evidência.
4. Numere RF-001, RNF-001; separe regras de negócio; gere user stories com CA;
   modele jornadas em Mermaid; monte a matriz de rastreabilidade.
5. Rode os `quality_gates` de `policies.yaml`; liste os que não passaram.
6. Encerre `software-specification.md` com `## Handoff Para Desenvolvimento`.

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
- Não feche decisão de produto sem confirmação do solicitante.
- Não use "A definir" quando há evidência no input — use `Pergunta Aberta`
  para lacunas reais e preencha com fatos quando há evidência.
