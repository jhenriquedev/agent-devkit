# Selenium Automation Builder

Agente especialista para automacoes Selenium/WebDriver seguras e revisaveis.

## Capabilities

- `plan-selenium-automation`: planeja automacao Selenium sem escrever arquivos.
- `generate-selenium-script`: gera script Python Selenium em modo output-only.
- `generate-selenium-project-files`: planeja ou grava pacote local com dry-run
  por padrao.
- `review-selenium-script`: revisa waits, seletores, screenshots, timeouts,
  credenciais e side effects.
- `wrap-selenium-as-capability`: gera wrapper de capability em dry-run por
  padrao.

## Contrato

```yaml
automation_name: Legacy Login Check
purpose: Check a legacy login page through WebDriver-compatible browser automation.
target_url: https://example.test/login
browser: chrome
remote_url_env: SELENIUM_REMOTE_URL
auth_strategy: env
side_effects: read-only
selenium_reasons:
  - webdriver-required
selectors:
  - name: username
    by: css
    value: '[name="username"]'
steps:
  - open target_url
  - wait for username
```

## Limites

Este agente nao instala Selenium, browsers ou drivers. Ele gera artefatos
revisaveis e scripts que fazem dry-run sem abrir browser.
