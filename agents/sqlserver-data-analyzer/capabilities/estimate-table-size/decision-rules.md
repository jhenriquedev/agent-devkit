# Decision Rules: Estimate Table Size

- Usar catalogos e DMVs read-only seguras para estimar tamanho e volume.
- Nao executar `DBCC`, maintenance, rebuild, update statistics ou comandos administrativos.
- Separar tamanho total, dados, indices e estimativa de linhas quando disponivel.
- Informar que estimativas podem estar defasadas.
- Nao consultar linhas de negocio para estimar tamanho.
- Aplicar filtros por schema/tabela quando informados.
- Nao expor connection string, host completo ou comentarios sensiveis.
- Aplicar timeout e `LOCK_TIMEOUT`.
- Usar resultado para orientar amostragem e limites de consultas futuras.
- Respeitar permissoes e reportar lacunas sem inferir inexistencia.
