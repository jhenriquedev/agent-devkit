# Prompt: Change Report

Objetivo: listar o historico de mudancas aplicadas pelo agente (ultimas 100 de
`<schema>.change_audit`). Operacao READ-ONLY.

Entradas: nenhuma obrigatoria (`--database` opcional).

Passos:
1. Chame `change-report`.
2. Apresente a tabela: id, operation, name, status, affected_rows, executed_at.
3. Use para auditar/confirmar que uma escrita foi registrada.

NAO faca: expor `metadata_json` cru se contiver caminhos/identificadores sensiveis;
tratar ausencia de linhas como erro (banco pode nunca ter sido alterado).
