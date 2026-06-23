# Prompt — Plan Migration

Objetivo: analisar um arquivo SQL de migration ANTES de qualquer execução e
expor o risco ao usuário.

Entradas: `--path` (arquivo `.up.sql`); opcional `--database`.

Raciocínio:
1. Rode o runner; leia checksum, statement_count, operations, blocked,
   destructive, transactional, rollback_path.
2. Resuma cada operação em linguagem clara (o que ela altera).

Rubrica de decisão:
- blocked == yes  -> declare que a migration NÃO poderá ser aplicada e por quê.
- destructive == yes && rollback_path == "-" -> avise que falta `.down.sql` e
  que apply será recusado.
- transactional == no -> destaque que rodará fora de transação.

Saída: o Markdown do template de plano (checksum, operações, flags, rollback).

NÃO faça: não aplique nada aqui; não esconda flags de risco; não imprima
connection string.
