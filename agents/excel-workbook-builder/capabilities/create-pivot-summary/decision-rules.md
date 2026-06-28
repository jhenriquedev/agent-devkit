# Regras

- Agrupar somente por colunas existentes e declaradas em `group_by`.
- Tratar resumo pivot-style como artefato derivado, preservando a fonte.
- Declarar agregacoes, contagens e campos de valor usados.
- Evitar totais que misturem tipos de dados incompatíveis.
- Gerar workbook `.xlsx` separado, sem sobrescrever fonte.
- Recomendar revisao visual quando a saida for usada como dashboard.
