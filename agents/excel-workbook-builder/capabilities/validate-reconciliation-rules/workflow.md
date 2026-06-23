# validate-reconciliation-rules

OBJETIVO: Validar as regras de conciliação (chave, colunas, tolerância) antes
de executar a conciliação, evitando falso positivo/negativo.

ENTRADAS: --left (JSON tabular); --right (JSON tabular); --key (colunas de
chave); --compare-column (repetível); --tolerance (float).

RACIOCÍNIO:
1. Carregue reconciliation-rules.md.
2. Valide: chave explícita e presente em ambas as bases, compare-columns
   presentes, tolerância >= 0.
3. Identifique riscos: tipos incompatíveis entre bases, escala diferente,
   colunas com muitos nulos.
4. Produza relatório de regras validadas e riscos identificados.

REGRAS DE DECISÃO:
- Chave ausente em qualquer base: bloqueante.
- Tipo incompatível em compare-column: aviso (reconciliação pode ser imprecisa).
- Tolerância negativa: bloqueante.

SAÍDA (markdown): validation-report.md com status pass/fail, regras validadas,
riscos e perguntas de negócio sugeridas.

NÃO FAZER: não executar a conciliação aqui; não silenciar riscos.
