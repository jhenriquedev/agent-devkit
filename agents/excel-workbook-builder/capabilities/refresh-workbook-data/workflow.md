# refresh-workbook-data  (DEPENDE DO RUNTIME NODE)

OBJETIVO: Substituir os dados de entrada de um workbook existente com nova
versão dos dados, mantendo fórmulas, resumos e layout.

ENTRADAS: --workbook (obrigatório); --input (JSON normalizado com novos dados);
--sheet (aba alvo); --output.

RACIOCÍNIO:
1. PRÉ-CHECK do runtime Node.
2. Inspecione o workbook atual para mapear abas de dados vs calculadas.
3. Substitua apenas as áreas de dados; preserva fórmulas e formatos.
4. Valide fórmulas dependentes com scan-formula-errors após refresh.

REGRAS DE DECISÃO:
- Se o schema dos novos dados diverge do schema original, reporte antes de
  aplicar.
- Nunca apague fórmulas em abas calculadas durante o refresh.

SAÍDA: workbook.xlsx com dados atualizados.

NÃO FAZER: não apagar fórmulas; não assumir compatibilidade de schema sem
verificar.
