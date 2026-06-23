# create-summary-dashboard  (DEPENDE DO RUNTIME NODE)

OBJETIVO: Criar uma aba executiva de dashboard com KPIs, gráficos e callouts
que referenciam dados do workbook.

ENTRADAS: --workbook (obrigatório); --output; --title; --kpi-config (JSON
opcional com métricas e fórmulas alvo).

RACIOCÍNIO:
1. PRÉ-CHECK do runtime Node.
2. Identifique KPIs e dimensões principais a partir dos dados ou do kpi-config.
3. Crie aba Dashboard com: métricas destacadas, gráficos referenciando Data,
   notas executivas.
4. Use fórmulas referenciando outras abas (carregue formula-rules.md); nunca
   embuta valores calculados como constantes.
5. Execute render-workbook-preview para conferência visual obrigatória.

REGRAS DE DECISÃO:
- KPIs não definidos: pergunte ao usuário antes de criar.
- Gráficos sem dados suficientes: avise e crie aba mesmo assim com nota.

SAÍDA: workbook.xlsx com aba Dashboard adicionada + preview.png.

NÃO FAZER: não hardcodar valores calculados; não criar dashboard sem definir
KPIs.
