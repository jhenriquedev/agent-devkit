# Decision Rules: List Tables

- Listar apenas metadados de tabelas e views acessiveis.
- Nao amostrar linhas ou consultar dados de negocio nesta capability.
- Filtrar por schema quando informado e declarar o schema usado.
- Separar `BASE TABLE`, `VIEW` e objetos equivalentes quando o catalogo permitir.
- Nao expor connection strings ou comentarios sensiveis.
- Respeitar permissoes e registrar resultados vazios sem inferir ausencia definitiva.
- Manter saida compacta para orientar `describe-table` e `sample-table`.
- Usar limites quando o catalogo retornar volume alto de objetos.
