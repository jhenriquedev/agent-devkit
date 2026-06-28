# Decision Rules: Generate ERD Report

- Gerar ERD a partir de metadados read-only de tabelas, PKs, FKs e relacionamentos inferidos.
- Diferenciar relacionamento declarado de relacionamento sugerido por nomes.
- Nao consultar ou renderizar valores de linhas.
- Limitar escopo por schema/tabelas para evitar diagramas ilegiveis.
- Mascarar nomes ou comentarios que revelem segredos quando detectados.
- Indicar relacionamentos ausentes por falta de FK declarada ou permissao.
- Nao criar ou alterar constraints no banco.
- A saida deve ser compativel com Mermaid/draw.io quando o template solicitar.
