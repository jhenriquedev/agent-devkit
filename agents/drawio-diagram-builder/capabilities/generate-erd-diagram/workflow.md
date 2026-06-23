# Workflow: Generate ERD Diagram

OBJETIVO: Gerar ERD (entidades, tabelas, chaves, relacionamentos, cardinalidade).

ENTRADAS: brief, fontes ou spec; output path.

RACIOCÍNIO:
1. Extraia entidades de construções "tabela/entidade X possui/tem/com ...".
2. Atributos terminando em _id viram FK → aresta para a entidade alvo.
3. Use frases de pertencimento (pertence a/referencia/relaciona com) para detectar
   relacionamentos explícitos.
4. kind=entity para todos os nós; leitura cima→baixo.
5. Rotule arestas com cardinalidade quando a fonte indicar (1:N, N:N, etc.).

DECISÃO: Não criar relação entre entidades que não existem na spec.

SAÍDA: erd.drawio + diagram-spec.json com diagram_type="erd".

NÃO FAZER: criar relacionamento entre entidades não mapeadas; omitir atributos _id
como FK; usar leitura esquerda→direita para ERD.
