# Workflow

1. Ler migrations e seed local.
2. Detectar tabelas em schema exposto sem RLS.
3. Detectar policies permissivas, `auth.role()`, `TO authenticated` sem
   ownership e UPDATE sem `WITH CHECK`.
4. Retornar findings read-only.
