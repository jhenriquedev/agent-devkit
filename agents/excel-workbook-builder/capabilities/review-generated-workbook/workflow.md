# review-generated-workbook

OBJETIVO: Revisar um workbook gerado quanto a abas obrigatórias, estrutura e
ausência de erros de fórmula — gate de qualidade bloqueante antes da entrega.

ENTRADAS: --workbook (caminho .xlsx obrigatório); --required-sheet (repetível);
--strict (falha em qualquer problema); --output.

RACIOCÍNIO:
1. Carregue o workbook via inspeção Python pura (sem Node).
2. Verifique presença de todas as abas em --required-sheet.
3. Execute scan de erros de fórmula (#REF!, #DIV/0!, #VALUE!, #NAME?, #N/A).
4. Verifique estrutura básica (cabeçalhos, tipos de dados, células vazias
   em campos obrigatórios).
5. Produza relatório com status pass/fail, abas faltantes e erros encontrados.

REGRAS DE DECISÃO:
- Com --strict: qualquer problema = status: fail; exit code 1.
- Sem --strict: erros de fórmula sempre bloqueam; abas faltantes geram aviso.
- Status: fail bloqueia exportação (export-workbook-artifacts não deve rodar).

SAÍDA (markdown): review.md com status, abas presentes/ausentes, erros de
fórmula listados, recomendações.

NÃO FAZER: não modificar o workbook; não exportar com status: fail.
