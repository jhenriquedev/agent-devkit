# Decision Rules

- Dry-run e o comportamento padrao.
- Escrita real exige `--execute` e confirmacao do runtime para `write_policy:
  confirm`.
- Nao escrever fora de `agents/<agent-id>/`.
- Nao sobrescrever agente existente sem permissao explicita.
- Nao criar providers, dependencias externas ou arquivos fora do contrato do
  agente.
