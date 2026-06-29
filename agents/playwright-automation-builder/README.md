# Playwright Automation Builder

Especialista em automacoes web modernas com Playwright.

## Capabilities

- `plan-playwright-automation`: planeja contrato, riscos, seletores e artifacts.
- `generate-playwright-script`: gera script Python Playwright em output-only.
- `generate-playwright-project-files`: planeja ou grava pacote local no projeto alvo.
- `run-playwright-check`: executa check local somente quando confirmado.
- `review-playwright-artifacts`: revisa screenshots, traces, logs e relatorios.
- `wrap-playwright-as-capability`: empacota automacao como capability local.

## Spec Minima

```yaml
automation_name: Login Smoke Check
purpose: Validar que a tela de login renderiza e exibe o botao Entrar.
target_url: https://example.test/login
browser: chromium
auth_strategy: none
side_effects: read-only
selectors:
  - name: submit
    kind: role
    value: button
    name_value: Entrar
steps:
  - open target_url
  - assert submit visible
assertions:
  - submit visible
artifacts:
  - screenshot
  - trace
quality_gates:
  - selectors prefer accessible roles
```

## Politica

Playwright e o caminho preferencial para web moderna sem requisito de
WebDriver/Grid. Selenium permanece para legado ou compatibilidade especifica.
