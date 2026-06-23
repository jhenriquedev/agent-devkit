# plan-workbook

OBJETIVO: Produzir um plano de workbook acionável (abas, tabelas, formulas,
gráficos, validações, quality gates, artefatos) a partir do brief.

ENTRADAS: --brief (obrigatório); --template-id (opcional); --data-schema (JSON
opcional com columns/types).

RACIOCÍNIO:
1. Extraia do brief: objetivo, público, granularidade, métricas-chave.
2. Derive abas: Inputs (parâmetros/premissas), Data (dados normalizados),
   Summary (KPIs), Quality (gates), e abas extras só se justificadas.
3. Para cada métrica derivada, especifique a formula auditável (carregue
   formula-rules.md): referência explícita, sem número mágico.
4. Liste validações de dados necessárias (listas, faixas, datas).
5. Defina quality gates concretos (abas obrigatórias, scan de erro, preview).

REGRAS DE DECISÃO:
- Se o brief não define chave/granularidade, pergunte antes de planejar.
- Se houver template-id, alinhe o plano ao sheet-map da versão atual.

SAÍDA (markdown): seções Brief, Abas (com propósito), Formulas (cell→formula→
fonte), Validações, Quality Gates, Premissas/Gaps.

NÃO FAZER: não gere o .xlsx aqui; não invente métricas fora do brief.

