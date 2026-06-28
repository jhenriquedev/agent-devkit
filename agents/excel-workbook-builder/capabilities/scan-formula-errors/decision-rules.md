# Regras

- Escanear workbook em modo read-only.
- Procurar erros `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?` e `#N/A`.
- Reportar sheet, celula ou contexto quando disponivel.
- Tratar erro de formula em area calculada como gate bloqueante para entrega final.
- Nao corrigir formulas nesta capability.
- Recomendar `add-formulas-and-validations` ou refinamento quando houver erro.
