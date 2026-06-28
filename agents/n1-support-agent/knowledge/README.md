# Knowledge

Conhecimento operacional do agente N1.

Esta pasta contem contexto, politicas, runbooks e prompts que orientam a
execucao deterministica do atendimento N1.

## Dominios

- `domains/customer-support/`: knowledge operacional generico usado para rotear
  sintomas, aplicar regras de negocio e montar o quality gate do diagnostico N1.

O carregamento deve ser sob demanda: primeiro o agente identifica a rota do
sintoma, depois usa apenas as regras do dominio selecionado.
