# AGENTS.md

Instrucoes especificas para agentes trabalhando em
`agents/aws-cloudwatch-log-analyzer/`.

## Papel do agente

Este agente e especialista em AWS CloudWatch Logs para sustentacao de servicos,
investigacao de erros, rastreio de requests, deteccao de padroes e relatorios
operacionais.

## Regras obrigatorias

- Codigo, nomes tecnicos, arquivos, classes, funcoes, variaveis e argumentos de
  CLI devem ser em ingles.
- Documentacao humana deve ser em portugues.
- Toda consulta real deve ter escopo explicito: regiao, log group e janela de
  tempo quando eventos forem consultados.
- Operacoes sao read-only no MVP.
- Nao consultar todas as regioes ou todos os log groups por padrao.
- Separar fatos vindos do CloudWatch de hipoteses do agente.
- Resumir payloads grandes em respostas humanas.
- Tratar logs como potencialmente sensiveis.

## Estrutura local

- `agent.yaml`: manifesto publico do especialista.
- `capabilities/`: capabilities executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: repository e contratos da integracao AWS CloudWatch.
