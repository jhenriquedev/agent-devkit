# Contexto

O Agent DevKit ja possui:

- `postgres-data-analyzer`: analise PostgreSQL generica read-only.
- `database-change-operator`: mudancas PostgreSQL com confirmacao.

Este agente cobre particularidades Supabase: schemas expostos via Data API, RLS,
Auth/JWT, Storage policies, Edge Functions, migrations Supabase e readiness de
CLI/MCP. O provider Supabase e opcional; a primeira fase funciona apenas com
arquivos locais.
