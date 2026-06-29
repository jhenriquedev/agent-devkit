# AGENTS.md

Instrucoes locais para trabalhar no agente `playwright-automation-builder`.

## Escopo

Este agente planeja, gera, revisa, executa checks locais controlados e empacota
automacoes Playwright para web moderna.

## Fronteiras

- Selenium/WebDriver legado pertence ao `selenium-automation-builder`.
- Automacoes desktop visuais pertencem ao `pyautogui-automation-builder`.
- Automacoes Python sem browser pertencem ao `python-automation-builder`.
- Execucao com side effects reais exige dry-run revisado e confirmacao.

## Guardrails

- Nunca hardcodar credenciais.
- Nunca versionar `storage_state` sensivel.
- Preferir seletores por role, label, text controlado ou test id.
- Evitar coordenadas, sleeps fixos, XPath absoluto e classes geradas.
- Capturar screenshots/traces como artifacts revisaveis.
