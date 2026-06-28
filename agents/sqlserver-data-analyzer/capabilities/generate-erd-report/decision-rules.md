# Decision Rules: Generate ERD Report

- Gerar ERD a partir de metadados read-only, PKs, FKs e relacionamentos inferidos.
- Diferenciar relacionamento declarado por constraint de relacionamento sugerido por heuristica.
- Nao consultar nem renderizar valores de linhas.
- Limitar escopo por database, schema ou lista de tabelas para evitar diagrama ilegivel.
- Mascarar comentarios ou nomes que exponham segredo quando detectados.
- Indicar relacionamentos ausentes por falta de FK ou permissao.
- Nao criar, alterar ou validar constraints por escrita.
- Aplicar `LOCK_TIMEOUT` e timeout nas consultas de catalogo.
- Manter output compativel com Mermaid quando usado.
- A saida deve ser revisavel por engenharia e dados sem acesso a dados pessoais.
