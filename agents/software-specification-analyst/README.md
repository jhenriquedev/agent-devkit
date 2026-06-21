# Software Specification Analyst

Agente especialista em analise de requisitos, descoberta funcional e criacao de
especificacoes completas para desenvolvimento de software.

## Escopo inicial

- conduzir entrevista guiada de requisitos;
- classificar a profundidade necessaria da analise;
- analisar um ou mais projetos/codigos existentes;
- criar documentos intermediarios de descoberta, contexto e impacto;
- levantar pontos criticos, riscos e duvidas de negocio;
- refinar analises com respostas e correcoes do usuario;
- gerar especificacao completa a partir de uma demanda ou dossie de analise;
- criar documentacao funcional;
- criar documentacao tecnica;
- escrever epicos, features, user stories e criterios de aceite;
- mapear jornadas e fluxos em Mermaid;
- montar matriz de rastreabilidade;
- revisar completude, ambiguidades e decisoes pendentes.

## Como usar

```bash
./ai-devkit capabilities software-specification-analyst
./ai-devkit run software-specification-analyst analyze-project-context --project . --output-dir specifications/contexto --yes-create-dir
./ai-devkit run software-specification-analyst conduct-requirements-interview --input demanda.md --analysis-dir specifications/contexto --output-dir specifications/entrevista --yes-create-dir
./ai-devkit run software-specification-analyst refine-analysis-with-feedback --analysis-dir specifications/contexto --feedback respostas.md --output-dir specifications/refinada --yes-create-dir
./ai-devkit run software-specification-analyst create-final-spec-from-analysis --analysis-dir specifications/refinada --output-dir specifications/final --yes-create-dir
./ai-devkit inspect software-specification-analyst create-complete-spec
./ai-devkit run software-specification-analyst create-complete-spec --input demanda.md
```

Por padrao, `create-complete-spec` propoe salvar os artefatos em:

```text
<projeto-atual>/specifications/<slug-da-demanda>/
```

Os runners perguntam antes de criar pastas. Para automacoes revisadas, use
`--yes-create-dir` explicitamente.

## Uso de skills em vendor

Antes de criar ou revisar uma especificacao, o agente deve consultar
`vendor/skills/CATALOG.md` e carregar apenas as skills cuja descricao casa com a
demanda. A skill principal de apoio e `vendor/skills/ecc/product-capability`.

Skills comuns por dominio:

- `vendor/skills/ecc/api-design`: APIs REST.
- `vendor/skills/ecc/backend-patterns`: backend.
- `vendor/skills/ecc/frontend-patterns`: frontend e telas.
- `vendor/skills/ecc/security-review`: auth, permissoes e dados sensiveis.
- `vendor/skills/ecc/tdd-workflow`: estrategia de testes.
- `vendor/skills/ecc/mcp-server-patterns`: MCP.
- `vendor/skills/ecc/mle-workflow`: machine learning.

## Artefatos gerados

Artefatos intermediarios de analise:

- `analysis-context.md`
- `project-architecture-notes.md`
- `business-rules-discovered.md`
- `critical-points.md`
- `business-questions.md`
- `technical-impact-analysis.md`
- `integration-map.md`
- `data-and-permissions-analysis.md`
- `open-decisions.md`
- `analysis-review.md`

Artefatos de entrevista e refinamento:

- `interview-guide.md`
- `stakeholder-questions.md`
- `missing-decisions.md`
- `refined-analysis.md`
- `resolved-questions.md`
- `remaining-open-questions.md`
- `decision-log.md`

Artefatos finais de especificacao:

- `software-specification.md`
- `functional-spec.md`
- `technical-spec.md`
- `user-stories.md`
- `journey-flows.md`
- `requirements-traceability.md`
- `open-questions.md`
