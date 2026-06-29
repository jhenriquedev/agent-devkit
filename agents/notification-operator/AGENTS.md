# AGENTS.md

Instrucoes especificas para o agente `notification-operator`.

- Mantenha notificacoes como contrato runtime pequeno, deterministico e seguro.
- Nao implemente canais remotos reais nesta fase; Slack, Teams, WhatsApp,
  webhooks e MCP gateways ficam apenas como canais futuros ate existir provider
  dedicado.
- Payloads devem seguir o evento canonico exposto por `cli.aikit.notifications`.
- Escritas locais de configuracao exigem capability explicita e nao devem
  armazenar segredos.
