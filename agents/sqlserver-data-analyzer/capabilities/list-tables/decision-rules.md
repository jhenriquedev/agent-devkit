# Decision Rules: List Tables

- Listar apenas metadados de tabelas e views acessiveis.
- Nao contar linhas, amostrar dados ou consultar conteudo de negocio nesta capability.
- Filtrar por schema quando informado e declarar o schema usado.
- Separar tabelas, views e objetos equivalentes quando o catalogo permitir.
- Nao expor connection string, host completo ou comentarios sensiveis.
- Respeitar permissoes e registrar resultado vazio sem inferir ausencia definitiva.
- Aplicar timeout e `LOCK_TIMEOUT`.
- Usar limites quando o catalogo retornar volume alto de objetos.
- Manter saida compacta para orientar `describe-table` e `sample-table`.
- Nao executar `sp_*` ou `EXEC` livre para descoberta.
