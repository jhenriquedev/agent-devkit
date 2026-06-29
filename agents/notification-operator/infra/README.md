# Infra

Este agente usa diretamente o modulo local `cli.aikit.notifications`.

Integracoes remotas futuras devem viver em `infra/integrations/<provider>/` e
ser expostas por capabilities separadas com politica de escrita explicita.
