# Prompt: test-connection

> Operação read-only. Mascare segredos. Separe dados coletados de inferências.

## Objetivo
Verificar se a conexão com o banco está operacional e coletar metadados básicos
(versão, database atual, usuário, schema) sem expor credenciais.

## Entradas esperadas
- `database` (opcional): nome do banco alvo (somente o nome, não URL).

## Passos de raciocínio
1. Execute `test-connection` com o `database` informado (ou padrão da env).
2. Confirme que o retorno contém `version`, `database`, `user_name`, `current_schema`.
3. Formate a saída com as informações recebidas.

## Regras de decisão
- **NUNCA** exiba a connection string, senha ou URL completa.
- Se o retorno vier vazio ou com erro, informe que a conexão falhou sem expor detalhes
  de credencial.
- `user_name` pode ser exibido (não é segredo); `password` jamais aparece aqui.

## Saída
```
# Postgres Connection
- Database: <database>
- User: <user_name>
- Schema: <current_schema>
- Version: <version resumida>
```

## NÃO faça
- Não exiba connection string, URL, senha ou token.
- Não infira capacidades do banco além do que o resultado confirma.
