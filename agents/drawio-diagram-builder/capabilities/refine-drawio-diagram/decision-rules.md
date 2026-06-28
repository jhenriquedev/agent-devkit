# Regras

- Preservar IDs de nodes, edges e grupos sempre que possivel para manter diffs e referencias do usuario.
- Aplicar feedback atualizando a spec antes de re-renderizar o `.drawio`.
- Registrar changelog com o que mudou, o que foi mantido e lacunas remanescentes.
- Validar XML, conectores, labels, geometria, titulo e legenda apos refinamento.
- Nao sobrescrever arquivo existente sem confirmacao por `yes_overwrite`.
- Nao remover informacao rastreavel da fonte sem justificar no changelog.
