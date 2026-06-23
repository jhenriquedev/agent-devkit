# Prompt: test-connection

## OBJETIVO
Confirmar conectividade com o SQL Server e capturar o contexto de execução atual
(versão, banco ativo, usuário, schema padrão).

## ENTRADAS
Nenhuma entrada obrigatória. Conexão vem de `SQLSERVER_DB_CONN_STRING`.

## RACIOCÍNIO (passos)
1. Execute a capability `test-connection`.
2. Leia os campos: `version`, `database_name`, `user_name`, `current_schema`.
3. Se a chamada retornar erro, identifique se é problema de credencial, rede ou
   string de conexão ausente.

## RUBRICA / REGRAS DE DECISÃO
- Conexão OK → confirme em 1–2 linhas com banco e schema ativos.
- Erro de conexão → reporte "falha de conexão" sem expor credenciais; sugira
  verificar `SQLSERVER_DB_CONN_STRING`.

## SAÍDA
Confirmação de conexão: banco ativo, schema padrão. Exemplo:
> Conectado ao banco `AdventureWorks` (schema padrão: `dbo`). SQL Server 2019.

## NÃO FAÇA
- Não imprima a connection string, host, usuário completo nem build interno
  completo da versão.
- Não exiba senhas, portas ou IPs.
