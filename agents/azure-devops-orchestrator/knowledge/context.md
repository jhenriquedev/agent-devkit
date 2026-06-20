# Azure DevOps Orchestrator Context

Este agente opera Azure DevOps Boards usando work items.

## Contexto minimo

- Work item e a entidade central.
- Cards devem ser identificados por ID sempre que possivel.
- Projeto Azure DevOps deve ser informado pela tarefa/capability; o `.env` pode
  conter projeto apenas como fallback local.
- Comentarios, tags, assignee, state e fields sao alteracoes rastreaveis.
- Boards e colunas podem variar por projeto; nao assuma nomes de colunas sem
  consultar o projeto.

## Regras de comportamento

- Leitura pode ser executada automaticamente.
- Escrita exige confirmacao explicita.
- Em lote, primeiro gerar plano, depois pedir confirmacao.
- Separar fatos coletados da API de inferencias ou recomendacoes.
- Preferir respostas estruturadas com contexto, riscos e proximos passos.

## Nao assumir

- Nao assumir que `Done`, `Closed`, `Resolved` ou `Ready` existem no processo.
- Nao assumir identidade de usuario por nome parcial.
- Nao remover tags sem listar as tags atuais e as tags a remover.
- Nao mover estado sem validar estados permitidos.
