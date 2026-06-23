# ingest-workbook-data

OBJETIVO: Extrair dados de um workbook .xlsx existente (abas e regiões
relevantes) para JSON normalizado.

ENTRADAS: --workbook (caminho .xlsx obrigatório); --sheet (aba alvo, opcional);
--output.

RACIOCÍNIO:
1. Carregue o workbook e liste as abas disponíveis.
2. Para a aba alvo (ou todas se não especificada), extraia cabeçalho e linhas.
3. Preserve valores numéricos como números, não texto formatado.
4. Registre metadados: aba, dimensões, arquivo de origem.

REGRAS DE DECISÃO:
- Aba não encontrada: falhe com erro claro e lista de abas disponíveis.
- Células mescladas: flatten para o valor da célula superior-esquerda.
- Não misture abas de dados com abas de fórmulas calculadas.

SAÍDA: extracted-data.json com columns, rows e metadados de origem por aba.

NÃO FAZER: não sobrescrever o workbook original; não inventar dados.
