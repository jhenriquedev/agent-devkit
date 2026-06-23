# ingest-source-document

OBJETIVO: Extrair dados tabulares de um documento fonte (CSV/TSV/JSON/MD/XLSX)
para JSON normalizado, roteando a fonte corretamente (carregue source-routing.md).

ENTRADAS: --source (caminho do documento obrigatório); --output; --encoding.

RACIOCÍNIO:
1. Identifique o tipo de fonte pelo conteúdo/extensão (carregue source-routing.md).
2. Para CSV/TSV/JSON/MD/XLSX local: ingira diretamente.
3. Para banco de dados: não processe aqui — delegue via request-database-data.
4. Para PDF/DOCX: exija conversão prévia; não processe formatos binários nativos.
5. Extraia dados em JSON tabular: {"source": ..., "columns": [...], "rows": [...]}.
6. Registre metadados de proveniência (arquivo origem, data de extração).

REGRAS DE DECISÃO:
- Se a fonte é banco de dados, pare e instrua o usuário a usar
  request-database-data.
- Se o formato não é suportado, reporte com instrução clara de conversão.
- Não silenciar linhas malformadas; reporte como aviso.

SAÍDA: extracted-data.json com columns, rows e metadados de origem.

NÃO FAZER: não conectar a banco; não silenciar erros de parsing; não inventar
dados faltantes.
