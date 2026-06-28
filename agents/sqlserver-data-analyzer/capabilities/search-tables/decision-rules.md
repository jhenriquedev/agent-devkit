# Decision Rules: Search Tables

- Buscar tabelas e views somente por metadados read-only.
- Usar padroes de nome, schema e tipo de objeto como criterios principais.
- Nao consultar linhas para provar que a tabela pertence a um dominio.
- Aplicar limite e ordenar resultados de forma deterministica.
- Respeitar permissoes; resultado vazio pode indicar falta de acesso.
- Nao expor connection string, host completo ou comentarios sensiveis.
- Aplicar timeout e `LOCK_TIMEOUT`.
- Marcar baixa confianca quando o match for apenas parcial.
- A saida deve orientar `describe-table`, `list-relationships` e `explore-database-domain`.
- Nao executar escrita ou procedures de descoberta.
