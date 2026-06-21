# Draw.io Diagram Builder Context

O agente transforma material bruto em diagramas editaveis. O fluxo padrao e:

1. carregar fontes;
2. fazer entrevista quando houver lacunas;
3. normalizar contexto;
4. produzir `diagram-spec.json`;
5. gerar `.drawio`;
6. revisar;
7. refinar ate aceite.

O formato intermediario `diagram-spec.json` e o contrato entre analise e
renderizacao. Ele deve ser simples, auditavel e versionavel.

## Fontes aceitas

- texto direto;
- arquivos Markdown, texto, JSON, YAML, CSV e HTML;
- PDF, DOCX, XLSX e PPTX por extracao textual;
- diretorios com multiplos arquivos;
- cards Azure DevOps por delegacao ao `azure-devops-orchestrator`;
- artefatos gerados por outros agentes do AI DevKit.

## Saidas padrao

- `source-context.json`;
- `diagram-plan.md`;
- `diagram-spec.json`;
- `diagram.drawio`;
- `diagram-review.md`;
- `open-questions.md`.
