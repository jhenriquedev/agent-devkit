# Decision Rules: Estimate Table Size

- Usar catalogos e estatisticas read-only para estimar tamanho e volume.
- Nao executar `VACUUM`, `ANALYZE`, `REINDEX` ou manutencoes administrativas.
- Separar tamanho total, tabela, indices e estimativa de linhas quando disponivel.
- Informar que estimativas podem estar defasadas se estatisticas estiverem antigas.
- Nao consultar linhas de negocio para estimar tamanho.
- Aplicar filtros por schema/tabela quando informados para reduzir ruido.
- Evitar expor nomes sensiveis fora do escopo solicitado.
- Usar resultado para orientar amostragem e limites de consultas futuras.
