# generate-workbook-from-data  (DEPENDE DO RUNTIME NODE)

OBJETIVO: Gerar um workbook .xlsx novo a partir de dados normalizados, sem
template base, criando as abas Summary, Data e Quality.

ENTRADAS: --input (JSON normalizado com columns/rows, obrigatório); --output
(caminho .xlsx obrigatório); --title; --sheet (default: Data).

RACIOCÍNIO:
1. PRÉ-CHECK do runtime Node (ver runtime.md): se indisponível, entregue
   o JSON normalizado e reporte o gap — não prometa .xlsx.
2. Valide os dados de entrada com validate-source-data antes de gerar.
3. Gere o workbook: aba Data (cabeçalho congelado, bordas), aba Summary (KPIs
   derivados), aba Quality (metadados e gates).
4. Após gerar, execute os quality gates obrigatórios: review-generated-workbook
   + scan-formula-errors + render-workbook-preview.
5. Só declare "entregue" se todos os gates passarem.

REGRAS DE DECISÃO:
- Dados inválidos (validate-source-data fail) = não gere o workbook.
- Gate com status fail = corrija a causa e regenere; nunca entregue com fail.
- Aba de dados alvo default = "Data"; confirme se diferente.

SAÍDA: workbook.xlsx no caminho --output.

NÃO FAZER: não gerar sem validar; não declarar sucesso com gate falho; não
usar Node sem pré-check.
