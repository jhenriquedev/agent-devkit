# create-template

OBJETIVO: Criar um template Excel inicial a partir de um brief, pronto para
versionamento e uso como base de geração de workbooks.

ENTRADAS: --brief (obrigatório); --template-id (slug do template);
--output (caminho do .xlsx de saída). Depende do runtime Node.

RACIOCÍNIO:
1. Leia o brief e identifique objetivo, público, abas e dados esperados.
2. Proponha estrutura de workbook: abas obrigatórias (Inputs, Data, Summary,
   Quality) e abas extras somente se justificadas pelo brief.
3. Liste validações e formulas necessárias (carregue formula-rules.md).
4. PRÉ-CHECK do runtime Node antes de gerar o .xlsx (ver runtime.md).
5. Gere o .xlsx; se Node indisponível, entregue o plano estruturado em .md
   e informe o gap explicitamente.
6. Solicite revisão antes de promover como versão validada.

REGRAS DE DECISÃO:
- Nunca grave o template no projeto sem --yes-save ou autorização explícita
  (write_policy: confirm).
- Se o brief não define abas ou dados, pergunte antes de gerar.

SAÍDA: template.xlsx no caminho --output (ou plano .md se Node ausente).

NÃO FAZER: não promover automaticamente; não gravar sem confirmação.
