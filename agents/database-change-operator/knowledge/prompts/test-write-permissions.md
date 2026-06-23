# Prompt — Test Write Permissions

Objetivo: validar se a connection string consegue escrever, SEM persistir dados.

Entradas: opcional `--database`, `--execute`.

Raciocínio:
1. Explique que o teste real usa tabela TEMPORÁRIA + insert/update/delete +
   rollback (nada é persistido).
2. Sem `--execute`: apenas liste os checks que seriam feitos.
3. Use esta capability ANTES de qualquer escrita real inédita no banco/target.

Rubrica:
- Se o teste falhar -> NÃO tente aplicar migration/update; reporte falta de
  permissão.
- Sucesso de conexão não implica permissão de escrita — só este teste confirma.

Saída: dry_run, write_permissions, rolled_back, checks.

NÃO faça: não infira permissão pelo connect; não persista dados de teste.
