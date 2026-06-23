# Prompt: Test Write Permissions

Objetivo: verificar se a connection string tem permissao de escrita, SEM efeito
colateral. Cria tabela temp, faz insert/update/delete e da `ROLLBACK`.

Entradas: `--execute` (para rodar o teste real; sem ele, apenas descreve os checks).

Passos:
1. Sem `--execute`: liste os checks que seriam feitos (`create_temp_table`,
   `insert`, `update`, `delete`).
2. Com `--execute`: rode o probe; resultado `write_permissions: true` +
   `rolled_back: true` confirma escrita disponivel sem alterar dados.

Use como PRIMEIRO passo ao operar um banco novo. NAO faca: interpretar falha como
problema de rede sem ler a mensagem de erro.
