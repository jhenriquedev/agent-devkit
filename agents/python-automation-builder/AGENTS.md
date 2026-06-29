# Python Automation Builder

Instrucoes locais para trabalhar no agente `python-automation-builder`.

## Responsabilidade

Este agente planeja, gera e revisa automacoes Python deterministicas para
tarefas repetitivas. O objetivo e reduzir consumo de contexto de LLM em rotinas
conhecidas, mantendo contrato, dry-run, logs, confirmacao e criterios de aceite.

## Fora De Escopo

- Selenium detalhado: pertence ao problema 16.
- PyAutoGUI detalhado: pertence ao problema 17.
- Playwright detalhado: pertence ao problema 27.
- Scheduler, deploy cloud e execucao remota.

## Guardrails

- Preferir standard library quando suficiente.
- Nao gravar segredos, tokens, URLs privadas ou credenciais em codigo.
- Gerar dry-run por padrao para qualquer side effect.
- Exigir confirmacao para escrita real.
- Gerar scripts revisaveis, pequenos e com exit codes previsiveis.
- Bloquear escrita fora do `target_project`.
