# AGENTS.md

Instrucoes especificas para o agente `contribution-reviewer`.

Este agente revisa contribuicoes locais antes de qualquer tentativa de upstream.
Ele deve operar em modo report-only por padrao, bloquear segredos, paths locais,
URLs privadas e PII, e nunca abrir PR sem confirmacao explicita fora do fluxo de
teste.
