# Prompt: Create Technical Spec

## OBJETIVO
Gerar especificação técnica detalhada cobrindo arquitetura, componentes, modelo
de dados, APIs, integrações, segurança, observabilidade, rollout e estratégia
de testes.

## ENTRADAS
- `input`: spec funcional, análise de projeto ou demanda. Obrigatório.
- Fonte esperada: fatos confirmados da análise e requisitos funcionais definidos.

## PASSOS DE RACIOCÍNIO
1. Identifique componentes impactados com base nos requisitos funcionais.
2. Para cada componente: responsabilidade, fronteiras, dependências.
3. Modelo de dados: entidades, atributos obrigatórios, classificação de
   sensibilidade, retenção, migrations necessárias.
4. APIs e contratos: endpoints, métodos, payloads, erros, versionamento.
5. Integrações: sistemas externos, protocolo, SLA, tratamento de falha.
6. Segurança: autenticação, autorização, segregação de papéis, auditoria,
   dados sensíveis.
7. Observabilidade: logs de eventos de negócio, métricas de sucesso/falha/
   latência, traces distribuídos, alertas.
8. Rollout e rollback: feature flag, migração, estratégia de rollback em
   produção.
9. Estratégia de testes: unitários (regras), integração (contratos), E2E
   (jornada principal), regressão (fluxos críticos).
10. Riscos técnicos e decisões em aberto.

## FORMATO DE SAÍDA
- **technical-spec.md**: resumo técnico, arquitetura (Mermaid de componentes),
  componentes (tabela), modelo de dados, APIs, integrações, segurança,
  observabilidade, rollout/rollback, estratégia de testes, riscos técnicos,
  decisões em aberto.

## NÃO FAÇA
- Não transforme sugestão técnica em decisão confirmada.
- Não defina stack sem evidência no input.
- Não omita estratégia de rollback quando há impacto em produção.
- Não classifique dado como não sensível sem evidência explícita.
