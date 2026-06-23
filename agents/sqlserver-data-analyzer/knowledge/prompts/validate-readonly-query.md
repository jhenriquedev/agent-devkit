# Prompt: validate-readonly-query

## OBJETIVO
Validar uma query SQL sem executá-la: verificar se é SELECT/WITH, bloquear
keywords proibidas e injetar TOP automático.

## ENTRADAS
- `query` (obrigatório): SQL a validar.
- `limit` (opcional, default 100): usado no TOP injetado.

## RACIOCÍNIO (passos)
1. Execute a capability `validate-readonly-query --query "<sql>"`.
2. Leia `valid` (boolean) e `query` (texto final com TOP injetado).
3. Se inválida, leia o `error` e identifique a causa (keyword bloqueada /
   não é SELECT).

## RUBRICA / REGRAS DE DECISÃO
- `valid: true` → query está apta para `run-readonly-query`.
- Keyword bloqueada → informe qual keyword e sugira reformular.
- Não é SELECT/WITH → informe e peça ao usuário para reformular.
- Use como gate **sempre que a query vier do usuário em texto livre**.

## SAÍDA
- Válida: `valid: true` + bloco SQL com TOP injetado.
- Inválida: descrição da causa + sugestão de correção.

## NÃO FAÇA
- Não execute a query — esta capability é apenas validação.
- Não contorne a validação mesmo que o usuário insista em uma query de escrita.
