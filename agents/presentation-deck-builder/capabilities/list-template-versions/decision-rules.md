# Decision Rules

- Listar versoes a partir de `templates/<template-id>/template.yaml`.
- Nao alterar manifest, status ou current version.
- Exibir status, caminho, created_at quando disponivel, notas e se a versao e atual.
- Preservar paths relativos para portabilidade.
- Sinalizar versoes referenciadas no manifest sem pasta correspondente.
- Sinalizar pastas de versao sem registro no manifest.
- Ordenar versoes de forma previsivel.
- Nao esconder versoes deprecated ou archived; apenas marcar status.
- Se template nao existir, retornar mensagem acionavel.
- A saida deve apoiar comparacao, promocao, deprecacao e geracao.
