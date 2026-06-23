OBJETIVO: Trazer contexto de um card Azure DevOps por delegação read-only.

ENTRADAS: id (obrigatório), project (opcional), include-comments (flag).

RACIOCÍNIO:
1. Valide que o id foi fornecido e é numérico.
2. Execute via azure-devops-orchestrator read-card (delegação read-only — nunca
   acesse Azure diretamente).
3. Do retorno, destaque: atores, sistemas, etapas, regras e critérios de aceite
   úteis para diagramar.
4. Salve como azure-card-context.md pronto para ingestão em ingest-diagram-sources.

RUBRICA/REGRAS DE DECISÃO:
- Nunca acesse Azure diretamente; se a delegação falhar, reporte o erro e pare.
- comments só incluídos quando --include-comments foi explicitamente solicitado.

SAÍDA: azure-card-context.md com título, descrição, atores, sistemas, etapas e
critérios de aceite estruturados.

NÃO FAZER: escrever no card; assumir inclusão de comentários sem --include-comments;
acessar Azure fora da delegação ao azure-devops-orchestrator.
