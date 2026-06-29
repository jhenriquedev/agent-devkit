# Decision Rules

- Capability gerada deve preservar dry-run por padrao.
- Capability com side effects deve usar `confirm`.
- Operacoes destrutivas continuam `blocked_by_default`.
- Runner gerado nao deve executar PyAutoGUI no import.
