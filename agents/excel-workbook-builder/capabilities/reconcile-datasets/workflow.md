# reconcile-datasets  (DEPENDE DO RUNTIME NODE para o .xlsx de resultado)

OBJETIVO: Conciliar duas bases tabulares por chave explícita, classificando
registros em matched/different/left_only/right_only.

ENTRADAS: --left (JSON ou CSV obrigatório); --right (JSON ou CSV obrigatório);
--key (colunas de chave, csv obrigatório); --compare-column (repetível);
--tolerance (float, default 0); --output.

RACIOCÍNIO:
1. Carregue reconciliation-rules.md antes de executar.
2. Execute validate-reconciliation-rules antes da conciliação: chave explícita,
   colunas presentes, tolerância >= 0.
3. Concilie as bases: matched (sem diferença), different (diferença dentro ou
   fora da tolerância), left_only, right_only.
4. Para o .xlsx de resultado: PRÉ-CHECK do runtime Node. Se ausente, entregue
   apenas o JSON de summary e o relatório .md.
5. Gere: reconciliation.xlsx (resumo + detalhe) e reconciliation-summary.json.

REGRAS DE DECISÃO:
- Chave não explícita: pare e pergunte antes de conciliar.
- Tolerância registrada no relatório sempre que > 0.
- left_only e right_only nunca devem ser silenciados.

SAÍDA: reconciliation.xlsx + reconciliation-summary.json + relatório .md.

NÃO FAZER: conciliar sem chave; suprimir left_only/right_only; aplicar ajustes.
