# Python Automation Builder

Agente especialista para criar automacoes Python seguras, revisaveis e
idempotentes quando possivel.

## Capabilities

- `plan-python-automation`: planeja contrato, risco, idempotencia, dependencias
  e artefatos sem escrever arquivos.
- `generate-python-automation`: gera um script Python em modo output-only.
- `generate-automation-project-files`: planeja ou grava um pacote local de
  automacao com dry-run por padrao.
- `review-python-automation`: revisa script contra dry-run, confirmacao, logs,
  segredos e erros.
- `wrap-automation-as-capability`: gera wrapper de capability do Agent DevKit em
  dry-run por padrao.

## Contrato

```yaml
automation_name: Report Cleanup
purpose: Clean old generated reports and summarize affected files.
inputs:
  - reports_dir
outputs:
  - summary_json
systems:
  - local filesystem
frequency: daily
risk: medium
target_environment: local workstation
side_effects: updates-local
dependencies:
  - pathlib
quality_gates:
  - dry-run lists affected paths
```

## Limites

Este agente cobre automacoes Python gerais. Automacoes com Selenium, PyAutoGUI
ou Playwright devem ser tratadas pelos agentes/specs especificos para esses
dominios.
