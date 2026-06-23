# Capability: Gerar Plano de Remediação (PLANO, não execução)

## Objetivo
Transformar achados consolidados num roteiro manual agrupado por severidade.

## Raciocínio
1. Agrupar findings por severidade (critical→info).
2. Para cada achado: ação proposta (recommendation) + passo de validação
   ("re-auditar read-only após remediação").

## Regras de decisão / gates
- Plano é SEMPRE manual/revisável; execução é "unsupported".
- Ordenar por severidade; critical primeiro.

## Saída
remediation-plan.md com o aviso explícito de que não executa correções.

## NÃO faça
NUNCA gere comandos destinados a rodar automaticamente como se fossem aplicados;
NUNCA afirme que a remediação foi feita.
