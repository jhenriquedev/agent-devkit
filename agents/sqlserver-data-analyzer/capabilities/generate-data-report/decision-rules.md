# Decision Rules: Generate Data Report

- Consolidar somente achados read-only ja coletados ou consultados com limites seguros.
- Incluir escopo, fonte, limites, qualidade de dados, sensibilidade e proximos passos.
- Nao expor dados sensiveis brutos, dumps de linhas ou credenciais.
- Separar fatos medidos de inferencias e recomendacoes.
- Declarar gaps de permissao, amostra insuficiente ou estatisticas desatualizadas.
- Usar agregados e exemplos mascarados para ilustrar problemas.
- Nao propor mutacao como passo executado; quando necessario, sugerir plano separado.
- Aplicar `TOP`, timeout e `LOCK_TIMEOUT` em qualquer consulta auxiliar.
- Bloquear escrita, `EXEC`, `DBCC`, `BACKUP`, `RESTORE` e DDL/DML.
- O relatorio deve ser revisavel por suporte, dados e engenharia.
