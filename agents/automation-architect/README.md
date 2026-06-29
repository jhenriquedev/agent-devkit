# Automation Architect

Agente especialista para classificar pedidos de automacao, escolher a tecnologia
adequada, planejar a solucao e indicar delegacao para builders especificos do
Agent DevKit.

## Capabilities

- `classify-automation-request`: classifica um pedido de automacao e recomenda
  abordagem, riscos e agente especializado.
- `plan-automation-solution`: gera plano de arquitetura da automacao, incluindo
  contrato, guardrails, alternativa e proximo passo.
- `delegate-automation-build`: retorna um contrato de delegacao manual para o
  builder adequado, sem executar o agente delegado.
- `review-automation-solution`: revisa plano ou solucao de automacao contra os
  guardrails do arquiteto.

## Exemplo

```bash
agent run automation-architect classify-automation-request \
  --request "automatize a coleta diaria de relatorios via API e salve CSV"
```

O agente deve escolher o caminho mais simples e robusto: API/CLI/repository antes
de browser, browser antes de desktop visual, e cloud/serverless apenas quando o
problema realmente pedir execucao event-driven ou gerenciada.
