# Decision Rules: Change Report

- Gerar relatorio a partir de historico de migrations, auditoria e backups.
- Nao executar mudancas de dados ou schema nesta capability.
- Filtrar por periodo, migration, objeto ou operador quando informado.
- Separar mudancas planejadas, aplicadas, falhas, rollbacks e backups.
- Nao expor connection string, senha, host completo ou URL completa.
- Mascarar valores sensiveis em previews de auditoria.
- Indicar linhas afetadas, status, timestamps e origem quando disponiveis.
- Reportar lacunas quando tabelas de historico nao existirem ou permissao faltar.
- Nao inferir sucesso de migration sem registro correspondente.
- A saida deve apoiar auditoria e decisao de rollback, nao substituir evidencia operacional.
