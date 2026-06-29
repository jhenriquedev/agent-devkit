# Supabase Project Analyst

Agente especialista em diagnostico read-only de projetos Supabase locais:
configuracao, migrations, RLS, Auth, Storage, Edge Functions e plano de
correcao sem executar alteracoes.

## Capabilities

- `inspect-supabase-project`: coleta contexto local e readiness de CLI/MCP.
- `audit-rls-policies`: audita RLS e policies em SQL local.
- `audit-auth-security`: audita Auth, claims e exposicao de secrets.
- `audit-storage-policies`: audita buckets/policies de Storage em SQL local.
- `review-migrations`: revisa migrations e DDL perigoso.
- `generate-supabase-report`: consolida findings em relatorio output-only.
- `plan-supabase-fix`: gera plano e SQL sugerido sem aplicar.

## Uso

```bash
./agent --json run supabase-project-analyst inspect-supabase-project --project-path .
```

Este agente nao executa SQL e nao aplica migrations.
