# Contexto

O runtime suporta canais locais `desktop`, `terminal`, `stdout` e `audit`.
`local` e alias de `desktop`; `console` e alias de `stdout`.

Canais remotos como Slack, Teams, WhatsApp, webhooks e MCP gateway aparecem no
catalogo como possibilidades futuras, mas nao sao implementados por este agente.

O payload canonico contem `event`, `status`, `task_id`, `title`, `summary`,
`artifacts`, `next_steps`, `severity`, `sensitive` e `origin`.
