# Selenium Automation Builder

Instrucoes locais para trabalhar no agente `selenium-automation-builder`.

## Responsabilidade

Este agente planeja, gera e revisa automacoes Selenium/WebDriver quando houver
motivo tecnico para preferir Selenium a Playwright: legado, Selenium Grid,
browser remoto corporativo, requisito WebDriver, extensoes de browser ou padrao
de equipe existente.

## Fora De Escopo

- Playwright moderno e validacao visual rica: problema 27.
- Automacao desktop com PyAutoGUI: problema 17.
- Criar Selenium Grid ou instalar browsers/drivers.
- Executar automacao real em browser durante geracao.

## Guardrails

- Exigir justificativa explicita para Selenium.
- Usar waits explicitos com `WebDriverWait`.
- Evitar `time.sleep` como mecanismo principal.
- Gerar dry-run por padrao para side effects.
- Exigir confirmacao para submissao, escrita externa ou acao destrutiva.
- Capturar screenshot em falha.
- Nao hardcodar credenciais.
