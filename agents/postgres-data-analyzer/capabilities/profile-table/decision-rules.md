# Decision Rules: Profile Table

- Perfilhar tabela com agregados read-only e limites seguros.
- Preferir estatisticas de nulos, distintos, min/max e tipos a linhas brutas.
- Nao despejar linhas brutas sensiveis.
- Mascarar ou omitir amostras de colunas pessoais quando usadas.
- Aplicar `statement_timeout` e adaptar estrategia para tabelas grandes.
- Registrar colunas puladas por risco, tipo nao suportado ou permissao.
- Separar perfil estatistico de interpretacao de negocio.
- A saida deve alimentar data quality, sensibilidade e relatorios.
