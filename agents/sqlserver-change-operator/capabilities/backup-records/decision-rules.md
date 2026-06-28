# Decision Rules: Backup Records

- Backup logico real exige `--execute`; sem a flag, retornar plano de backup.
- Fazer backup apenas de registros dentro de escopo, filtro e limite definidos.
- Exigir `WHERE` seguro ou identificadores especificos para evitar copia ampla acidental.
- Registrar backup em tabela de historico no schema configurado.
- Nao usar `BACKUP DATABASE`, `RESTORE`, comandos de servidor ou arquivos externos.
- Mascarar dados sensiveis em saidas humanas e previews.
- Aplicar timeout, lock timeout e limite de linhas afetadas/copias.
- Preservar colunas necessarias para rollback logico quando aplicavel.
- Nunca imprimir connection string, senha, host completo ou URL completa.
- Se o backup for pre-condicao de update/delete, bloquear a mudanca quando backup falhar.
