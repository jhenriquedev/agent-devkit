# Regras

- Processar CSV, TSV, JSON, XLSX simples, PDF ou DOCX conforme roteamento suportado.
- Tratar fonte como read-only e registrar caminho, formato e limites de extracao.
- Extrair tabelas apenas quando a estrutura for suficientemente clara.
- Separar dados extraidos de inferencias sobre significado das colunas.
- Mascarar dados sensiveis em amostras quando houver risco de exposicao.
- Gerar `extracted-data.json` como artefato derivado.
