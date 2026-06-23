# inspect-template

OBJETIVO: Inspecionar a estrutura interna de um template .xlsx (abas, regiões
usadas, fórmulas, validações, tabelas, erros) para informar planejamento e
decisões de promoção.

ENTRADAS: --workbook (caminho do .xlsx obrigatório); --output.

RACIOCÍNIO:
1. Carregue o workbook via inspeção XML (Python puro, sem Node).
2. Liste abas presentes e suas dimensões.
3. Conte e liste fórmulas, validações de dados e tabelas.
4. Detecte marcadores de erro (#REF!, #DIV/0!, #VALUE!, #NAME?, #N/A).
5. Produza relatório com riscos, lacunas e áreas protegidas.

REGRAS DE DECISÃO:
- Erros de fórmula detectados devem ser listados explicitamente.
- Áreas editáveis vs calculadas vs protegidas devem ser separadas.

SAÍDA (markdown): seções Abas, Fórmulas, Validações, Tabelas, Erros, Riscos.

NÃO FAZER: não modificar o workbook; não usar Node para inspeção.
