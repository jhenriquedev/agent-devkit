# Providers

Use lazy provider configuration.

1. Identify `requires.providers` for the chosen capability.
2. Check status with `agent provider status <provider> --json` when local tools
   are available.
3. If missing, ask only for the minimum reference needed now:
   `--env NAME`, `--env-file PATH`, native profile, or session-only context.
4. If the user ignores the request, preserve the declared fallback.

Valid fallbacks:

- `plan_only`
- `dry_run`
- `manual_steps`
- `use_user_supplied_context`
- `skip_provider`
- `blocked`

Never print raw values from API keys, passwords, PATs, tokens, connection
strings, or private keys.
