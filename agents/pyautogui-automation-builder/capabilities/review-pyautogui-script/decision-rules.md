# Decision Rules

- Script sem `pyautogui.FAILSAFE = True` falha na revisao.
- Script com side effects precisa de `--execute` e `--confirm`.
- Script deve expor `--dry-run`, `--screenshot-dir`, `--timeout` e
  `--abort-file`.
- Script deve capturar screenshot antes/depois/erro.
- Coordenadas absolutas sem regiao/validacao devem gerar finding.
