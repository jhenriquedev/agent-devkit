# Workflow

1. Resolver `project-path` ou usar diretorio atual.
2. Ler `supabase/config.toml`, migrations, seed e Edge Functions se existirem.
3. Opcionalmente executar apenas `supabase --version`, `supabase --help` e
   `supabase db --help` com timeout.
4. Redigir qualquer segredo antes de retornar.
