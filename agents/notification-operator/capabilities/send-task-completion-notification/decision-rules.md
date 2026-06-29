# Decision Rules

- Envio exige `--confirm`.
- Canais locais suportados sao `desktop`, `terminal`, `stdout` e `audit`.
- Canais remotos devem retornar estado controlado, sem tentar envio real.
- Falha de entrega nao deve ocultar payload canonico nem historico local.
