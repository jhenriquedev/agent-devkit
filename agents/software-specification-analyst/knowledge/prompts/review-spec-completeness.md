# Prompt: Review Spec Completeness

## OBJETIVO
Auditar uma especificação existente contra os `quality_gates` e as 21 seções
de `specification_policy`, apontando lacunas, ambiguidades, contradições,
seções ausentes e perguntas que bloqueiam a implementação.

## ENTRADAS
- `input`: especificação (Markdown). Obrigatório.
- `strictness`: `lenient` | `standard` | `strict` (default `standard`).

## PASSOS DE RACIOCÍNIO
1. Cheque presença das 21 seções de `specification_policy.required_sections`
   em `knowledge/policies.yaml`. Marque ausentes.
2. Para cada `quality_gate` de `policies.yaml`, marque:
   - `PASS` — critério atendido, com evidência citada.
   - `PARCIAL` — atendido parcialmente; descreva o que falta.
   - `FALHA` — critério não atendido; descreva o problema e a ação necessária.
3. Detecte problemas de qualidade:
   - Ambiguidades: termos vagos ("deve ser rápido", "deve funcionar bem").
   - Contradições: requisitos conflitantes entre seções.
   - Requisitos sem CA verificável.
   - CA sem teste mapeado (apenas em `strict`).
   - Regras de negócio implícitas não validadas.
4. Em `strict`: exija rastreabilidade RF/RNF ↔ US ↔ CA ↔ teste completa.
5. Produza veredito: `LIBERÁVEL PARA IMPLEMENTAÇÃO` ou
   `REQUER CORREÇÕES` + lista de bloqueios.

## RUBRICA DE VEREDITO
- `LIBERÁVEL`: todos os gates `PASS` ou `PARCIAL` sem bloqueante; todas as 21
  seções presentes; sem ambiguidade ou contradição grave.
- `REQUER CORREÇÕES`: qualquer gate em `FALHA` bloqueante; seção obrigatória
  ausente; contradição grave; pergunta bloqueante sem resposta.

## FORMATO DE SAÍDA
- Tabela de gates: `Gate | Status | Evidência | Ação necessária`.
- Lista de seções ausentes.
- Lista priorizada de correções (bloqueantes primeiro).
- Veredito final com justificativa.

## NÃO FAÇA
- Não dê `LIBERÁVEL` se houver gate em `FALHA` bloqueante.
- Não invente problema que não está na spec.
- Não sugira solução — apenas aponte a lacuna e a ação.
