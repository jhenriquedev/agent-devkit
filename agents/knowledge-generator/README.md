# Knowledge Generator

Agente especialista em criar uma pasta `knowledge/` a partir de fontes variadas,
incluindo repositorios de codigo, arquivos soltos, documentacoes, PDFs, HTML,
planilhas, apresentacoes e conjuntos mistos.

## Escopo inicial

- inspecionar arquivos e pastas;
- detectar tipos comuns de codigo, incluindo Python, TypeScript, C#, Flutter,
  Dart, HTML e CSS;
- carregar documentos de texto, Markdown, JSON, YAML, XML, HTML, PDF, DOCX,
  XLSX, CSV e PPTX quando possivel;
- escolher profiles como `code-project`, `frontend-app`, `documentation-set`,
  `integration-docs`, `business-domain`, `support-operations`, `data-domain`,
  `mixed-knowledge` e `freeform`;
- gerar knowledge com rastreabilidade por fonte;
- validar artefatos gerados e reportar lacunas.

## Como usar

```bash
agent capabilities knowledge-generator
agent run knowledge-generator list-knowledge-profiles
agent run knowledge-generator inspect-source --source ./projeto
agent run knowledge-generator generate-knowledge --source ./projeto --output-dir ./knowledge --yes-create-dir
agent run knowledge-generator validate-knowledge --knowledge-dir ./knowledge
```

## Politica de saida

Os artefatos gerados dependem do profile escolhido. Projetos de codigo podem
gerar inventario de codigo; documentacoes podem gerar conceitos, glossario e
decisoes; fontes mistas combinam indices, fatos, lacunas e inventarios
especificos quando houver evidencia suficiente.
