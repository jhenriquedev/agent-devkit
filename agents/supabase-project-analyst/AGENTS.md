# Supabase Project Analyst

Instrucoes locais para trabalhar no agente `supabase-project-analyst`.

## Responsabilidade

Este agente analisa projetos Supabase em modo read-only, com foco em Postgres,
RLS, Auth, Storage, Edge Functions, migrations, performance e seguranca. A
primeira fase analisa arquivos locais e readiness de CLI/MCP sem aplicar SQL.

## Fora De Escopo

- Aplicar migrations.
- Executar SQL real.
- Criar projeto Supabase.
- Alterar RLS, Auth, Storage ou configuracao remota.
- Armazenar credenciais OAuth/token.
- Substituir `postgres-data-analyzer` para analise SQL generica.

## Guardrails

- Nunca imprimir `service_role`, access token, DB URL ou JWT secret.
- Nunca usar `raw_user_meta_data`/`user_metadata` como autorizacao segura.
- Alertar para tabelas expostas sem RLS.
- Alertar para `auth.role()`, `TO authenticated` sem ownership e UPDATE sem
  `WITH CHECK`.
- Alertar para `SECURITY DEFINER` em schema exposto e views sem
  `security_invoker`.
- Gerar SQL apenas como sugestao, nunca aplicar.
