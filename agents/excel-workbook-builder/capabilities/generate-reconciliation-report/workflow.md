# generate-reconciliation-report  (DEPENDE DO RUNTIME NODE para .xlsx)

OBJETIVO: Gerar um relatório completo de conciliação em .xlsx e .md a partir
dos resultados de reconcile-datasets.

ENTRADAS: --reconciliation-summary (JSON obrigatório); --reconciliation-data
(JSON com detalhes, opcional); --output.

RACIOCÍNIO:
1. Leia o reconciliation-summary.json produzido por reconcile-datasets.
2. PRÉ-CHECK do runtime Node para geração do .xlsx.
3. Crie workbook com abas: Resumo (totais por classe), Matched, Different,
   Left_Only, Right_Only.
4. Adicione notas de tolerância e metadados de conciliação.
5. Gere também relatório .md narrativo.

REGRAS DE DECISÃO:
- Se Node ausente: entregue o .md narrativo e reporte o gap do .xlsx.
- Não omita left_only/right_only mesmo se vazios (mostre aba com "Nenhum").

SAÍDA: reconciliation.xlsx + reconciliation-report.md.

NÃO FAZER: não omitir classes vazias; não gerar .xlsx sem pré-check do Node.
