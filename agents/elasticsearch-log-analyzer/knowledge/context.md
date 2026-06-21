# Contexto

- O agente analisa logs no Elasticsearch sem fixar projeto ou source no `.env`.
- O escopo de negocio deve ser informado por `--source`, `--service`,
  `--environment`, periodo e filtros.
- `source` pode ser indice, data stream, alias ou pattern.
- Operacoes sao read-only.
- Para evitar consumo excessivo, sempre use limites e agregacoes antes de
  carregar muitos eventos.
- Relatorios devem separar fatos coletados de inferencias.
