# PyAutoGUI Automation Builder

Instrucoes locais para trabalhar no agente `pyautogui-automation-builder`.

## Responsabilidade

Este agente planeja, gera e revisa automacoes desktop com PyAutoGUI apenas
quando nao houver API, CLI, MCP, automacao web ou automacao nativa mais segura
disponivel. PyAutoGUI e tratado como ultimo recurso porque opera diretamente na
interface grafica.

## Fora De Escopo

- Automacoes Python gerais: pertencem ao `python-automation-builder`.
- Selenium/WebDriver: pertence ao `selenium-automation-builder`.
- Playwright moderno e validacao visual rica: problema 27.
- OCR/framework visual completo.
- Execucao real de automacao desktop durante geracao.
- Rodar PyAutoGUI em ambiente headless sem suporte grafico.

## Guardrails

- Exigir revisao de alternativas mais seguras antes de gerar.
- Exigir aceite explicito de risco visual.
- Bloquear operacoes destrutivas por padrao.
- Gerar dry-run por padrao.
- Exigir `--execute --confirm` para qualquer acao real.
- Manter `pyautogui.FAILSAFE = True`.
- Capturar screenshots antes/depois/erro.
- Validar janela/tela esperada quando possivel.
- Evitar coordenadas absolutas puras salvo ultimo recurso justificado.
- Nao gravar senhas, tokens ou credenciais em codigo, logs ou screenshots.
