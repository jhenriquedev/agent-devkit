# Decision Rules: Run Integration Tests

- Sem `--execute`, nenhuma chamada externa e realizada.
- Mutations reais exigem `--confirm-mutations`.
- Sem base URL ou ambiente seguro, bloquear execucao real.
- Mascarar secrets em requests e respostas.
