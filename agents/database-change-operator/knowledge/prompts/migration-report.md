# Prompt — Migration Report

Objetivo: listar o histórico de migrations de `ai_devkit_migrations`.

Entradas: opcional `--database`.

Raciocínio:
1. Use antes de aplicar (ver o que já existe) e depois (confirmar registro).
2. Use para validar que um rollback foi registrado (`status = rolled_back`).

Saída: tabela id/name/status/applied_at/rollback.

NÃO faça: não exponha credenciais nem connection string; relatório é objetivo.
