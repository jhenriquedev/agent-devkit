# Context

O estado dos wizards fica em `~/.agent-devkit/state/wizards`. A configuracao
final de source fica em `~/.agent-devkit/config.json` com referencias seguras.
`~/.ai-devkit` continua aceito como home legado quando ja existir.

Este agente e global: nenhum agente de dominio deve implementar seu proprio
fluxo de credencial hardcoded.
