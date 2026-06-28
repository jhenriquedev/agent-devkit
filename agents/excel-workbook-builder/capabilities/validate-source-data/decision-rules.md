# Regras

- Validar colunas obrigatorias, tipos, duplicidades, blanks e regras do schema esperado.
- Tratar validacao como read-only; nao corrigir a fonte.
- Separar erro bloqueante de aviso.
- Reportar exemplos limitados e mascarar dados sensiveis.
- Nao inferir schema esperado quando `expected_schema` for insuficiente; registrar lacuna.
- Recomendar normalizacao antes de gerar workbook quando tipos estiverem inconsistentes.
