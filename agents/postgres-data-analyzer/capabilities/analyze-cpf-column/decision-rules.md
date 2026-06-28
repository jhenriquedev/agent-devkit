# Decision Rules: Analyze CPF Column

- Executar apenas consultas read-only sobre a coluna CPF indicada.
- Validar schema, tabela e coluna antes de montar qualquer consulta.
- Usar agregados para formato invalido, digitos repetidos, digito verificador e duplicidade.
- Nao exibir CPFs completos; quando amostra for indispensavel, mascarar por padrao.
- Aplicar `statement_timeout` e limites compativeis com o tamanho da tabela.
- Separar problemas de formato, problemas de qualidade e duplicidades de documento.
- Nao corrigir dados, normalizar tabela ou deduplicar registros nesta capability.
- Alertar quando a coluna analisada tiver semantica incerta ou puder conter CNPJ/documento misto.
