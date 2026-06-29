# PyAutoGUI Automation Builder

Agente especialista para automacoes desktop visuais com PyAutoGUI, usadas como
ultimo recurso quando API, CLI, MCP, Playwright, Selenium ou automacao nativa do
sistema operacional nao resolvem a tarefa.

## Capabilities

- `plan-desktop-automation`: planeja automacao desktop sem escrever arquivos.
- `generate-pyautogui-script`: gera script PyAutoGUI em modo output-only.
- `generate-pyautogui-project-files`: planeja ou escreve pacote local de
  automacao.
- `review-pyautogui-script`: revisa guardrails de um script PyAutoGUI.
- `wrap-pyautogui-as-capability`: empacota automacao aprovada como capability.

## Contrato De Entrada

Specs YAML/JSON devem informar:

- `automation_name`
- `purpose`
- `target_app`
- `target_window`
- `platform`
- `steps`
- `screen_preconditions`
- `verification_strategy`
- `safer_alternatives_checked`
- `user_accepts_visual_risk`
- `side_effects`
- `coordinates_policy`

## Exemplo

```bash
./agent --json run pyautogui-automation-builder plan-desktop-automation \
  --spec desktop-spec.yaml
```

## Politica

Scripts gerados nao executam a automacao por padrao. A execucao real exige
`--execute --confirm`, screenshots e validacao visual basica. Operacoes
destrutivas sao bloqueadas no planejamento.
