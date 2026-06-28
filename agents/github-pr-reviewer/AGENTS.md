# AGENTS.md

Instrucoes locais para o agente `github-pr-reviewer`.

Este agente opera em modo conservador por padrao:

- leitura de PRs e diffs e permitida quando `gh` estiver autenticado;
- comentarios, aprovacao e request changes exigem opt-in explicito;
- automacoes nascem `report-only`;
- nunca aprove PR sem diff completo e checks obrigatorios conhecidos.
