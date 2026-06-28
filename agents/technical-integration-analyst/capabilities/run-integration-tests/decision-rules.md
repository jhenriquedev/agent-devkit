# Decision Rules: Run Integration Tests

- Sem `--execute`, nenhuma chamada externa e realizada.
- Mutations reais exigem `--confirm-mutations`.
- Sem base URL ou ambiente seguro, bloquear execucao real.
- Mascarar secrets em requests e respostas.
- Execucao real exige `--execute` e host permitido por `--allow-host` ou `TECH_INTEGRATION_ALLOWED_HOSTS`.
- Bloquear metadata service, loopback, localhost, IP privado nao autorizado e schemes nao HTTP/HTTPS.
- Gerar plano de execucao antes de qualquer chamada real.
- Respeitar timeout padrao ou informado; nao fazer retry agressivo sem contrato.
- Executar operacoes na ordem de fluxo quando houver dependencias.
- Em dry-run, marcar mutations e mostrar request planejado com variaveis.
- Nao executar mutation em ambiente produtivo sem confirmacao especifica e ambiente explicito.
- Relatorio deve incluir status por operacao, base URL mascarada quando necessario e lacunas.
