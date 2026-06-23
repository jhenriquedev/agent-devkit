# update-existing-workbook  (DEPENDE DO RUNTIME NODE)

OBJETIVO: Atualizar a aba de dados de um workbook existente com novos dados,
preservando estrutura, fórmulas, estilos e demais abas.

ENTRADAS: --workbook (obrigatório); --input (JSON normalizado); --sheet (aba
alvo, default: Data); --output.

RACIOCÍNIO:
1. PRÉ-CHECK do runtime Node (ver runtime.md).
2. Inspecione o workbook atual com inspect-template antes de editar.
3. Substitua somente a aba alvo; preserve layout, fórmulas e estilos.
4. Execute quality gates após atualizar.

REGRAS DE DECISÃO:
- Fórmulas que dependem da aba alvo podem ser afetadas: verifique com
  scan-formula-errors após a atualização.
- Dados de entrada maiores que o range esperado: reporte e confirme expansão.

SAÍDA: workbook.xlsx atualizado.

NÃO FAZER: não tocar abas fora da alvo; não assumir que fórmulas existentes
continuarão válidas sem verificar.
