# create-template-version

OBJETIVO: Criar uma nova versão de template versionada a partir de um arquivo
base ou versão anterior, sem sobrescrever versões existentes.

ENTRADAS: --template-id (obrigatório); --version (obrigatório, ex: 1.1.0);
--template (arquivo .xlsx) ou --base-version; --status (default: draft);
--templates-root; --feedback.

RACIOCÍNIO:
1. Liste o estado atual com list-template-versions antes de versionar.
2. Confirme que a versão alvo não existe no manifest.
3. Crie a pasta versions/<version> e copie o template.
4. Atualize o manifest (com data de criação via date.today().isoformat()).
5. Gere artefatos auxiliares: sheet-map, input-schema, usage-notes, changelog.

REGRAS DE DECISÃO:
- NUNCA sobrescreva uma versão já existente no manifest (falha com erro claro).
- Ajuste = nova versão; use refine-template se o usuário quer iterar sobre
  uma versão existente.
- Status inicial deve ser "draft"; somente promote-template-version define
  "validated".

SAÍDA: pasta versions/<version>/ com template.xlsx, sheet-map, input-schema,
usage-notes e changelog atualizados.

NÃO FAZER: não criar versão duplicada; não promover automaticamente.
