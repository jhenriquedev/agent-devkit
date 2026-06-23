# Prompt: Run Write Script

Objetivo: executar um script T-SQL de escrita controlado, dry-run por padrao,
dentro de transacao quando possivel.

Entradas: `--path` (obrigatorio); `--execute`.

Passos:
1. Dry-run: apresente plano (operacoes, risco, transacional?).
2. `blocked: yes` -> PARE e explique a keyword.
3. Se `transactional: no` (ex.: contem BACKUP/RESTORE/ALTER DATABASE) -> alerte que
   nao rodara em transacao; avalie risco com o usuario.
4. Confirme; execute com `--execute`.

NAO faca: executar script com keyword bloqueada; rodar sem revisar operacoes nao
transacionais.
