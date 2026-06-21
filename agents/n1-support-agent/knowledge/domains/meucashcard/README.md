# Knowledge MeuCashCard

Este diretorio concentra conhecimento operacional do dominio MeuCashCard para o
`n1-support-agent`.

O objetivo nao e carregar todo o legado em todo atendimento. O agente primeiro
classifica o sintoma, depois carrega apenas as regras, playbooks e contratos
necessarios para interpretar o problema do cliente.

## Estrutura

- `index.json`: indice de dominios, rotas e arquivos condicionais.
- `symptom-routing.json`: roteamento de sintomas para checks minimos.
- `contracts/`: contratos de saida e quality gates.
- `playbooks/`: roteiros operacionais reutilizaveis.
- `rules/`: regras de negocio normalizadas por dominio.

## Politica

- CPF e dados pessoais devem ser mascarados em saidas humanas.
- Segredos e connection strings nao devem ser copiados para knowledge.
- Regras de negocio devem citar a origem em `source` quando vierem de codigo ou
  knowledge legado.
