# Prompt: Plan Migration

Objetivo: analisar um arquivo de migration SQL Server ANTES de qualquer execucao.
Operacao READ-ONLY: nunca aplica nada.

Entradas esperadas:
- `--path` (obrigatorio): caminho do arquivo `.up.sql`.

Passos de raciocinio:
1. Chame `plan-migration --path <arquivo>`.
2. Leia o plano: `checksum`, `statement_count`, `operations[]`, `blocked`,
   `destructive`, `transactional`, `rollback_path`, `risk_level`.
3. Resuma para o usuario: o que a migration faz, o risco, se ha rollback detectado
   (`.down.sql` ao lado do `.up.sql`).

Regras de decisao:
- `blocked: yes` -> avise que a migration NAO podera ser aplicada (keyword
  bloqueada) e qual comando a disparou.
- `destructive: yes` e `rollback_path` ausente -> alerte que `apply-migration`
  exigira `--rollback-path`.

Saida: apresente o plano renderizado e o proximo passo (`apply-migration --execute`).
NAO faca: sugerir execucao sem o usuario revisar; inventar conteudo do arquivo.
