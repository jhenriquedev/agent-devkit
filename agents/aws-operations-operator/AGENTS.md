# AGENTS.md

Instrucoes especificas para agentes trabalhando em `agents/aws-operations-operator/`.

## Papel do agente

Este agente executa operacoes AWS controladas. O comportamento padrao e dry-run:
ele planeja e mostra o comando, mas nao altera recursos. Execucao real exige
`--execute`, `--confirm-resource` igual ao recurso alvo e ambiente explicito.

## Regras obrigatorias

- Dry-run e o padrao para todas as capabilities.
- Escrita real exige `--execute`.
- Escrita real exige `--confirm-resource`.
- Producao deve ser informada como `--environment prd`; aliases como `prod`
  nao liberam execucao.
- Operacoes destrutivas ficam bloqueadas por padrao.
- Todo comando AWS deve estar na allowlist do repository.
- Toda execucao real deve gerar `operation-result.json` e relatorio.
- Nunca imprimir secrets, payloads sensiveis ou respostas volumosas sem resumo.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: operacoes controladas.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de plano, rollback e relatorio.
- `infra/`: repository AWS operations, renderers e validações.
