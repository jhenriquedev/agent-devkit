# Prompt: Rollback Migration

Objetivo: executar o `.down.sql` de uma migration, dry-run por padrao.

Entradas: `--path` (obrigatorio, o arquivo `.down.sql`); `--execute`.

Passos:
1. Dry-run: apresente o plano do rollback.
2. Se `blocked: yes` -> PARE.
3. Confirme com o usuario que reverter e a intencao (perda de schema/dados pode
   ocorrer).
4. Execute com `--execute`. Registra `operation_type=rollback` em `change_audit`.

NAO faca: rodar rollback sem confirmar impacto; assumir que o rollback e seguro so
porque existe arquivo.
