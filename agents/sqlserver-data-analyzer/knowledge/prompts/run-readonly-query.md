# Prompt: run-readonly-query

## OBJETIVO
Executar uma query SELECT bounded, retornando linhas com mascaramento de PII.

## ENTRADAS
- `query` (obrigatório): SQL SELECT ou WITH.
- `limit` (opcional, default 100): limite de linhas via TOP automático.
- `database` (opcional): banco alvo.

## RACIOCÍNIO (passos)
1. Se a query vier do usuário em texto livre, rode `validate-readonly-query`
   primeiro para confirmar que é segura.
2. Execute a capability `run-readonly-query --query "<sql>"`.
3. O runner aplica automaticamente `validate_readonly_query` (bloqueia keywords
   de escrita) e `enforce_top` (injeta `TOP (limit)` se ausente).
4. Leia `row_count`, `limit` e `rows[]`.
5. Identifique colunas sensíveis no resultado; aplique mascaramento se necessário.

## RUBRICA / REGRAS DE DECISÃO
- Query vem do usuário → use `validate-readonly-query` antes.
- Query construída por `build-analysis-query` → pode ir direto.
- `row_count == limit` → pode haver mais linhas; informe e sugira WHERE mais
  específico.
- Colunas com `sensitive_kind != null` → mascarar na saída.

## SAÍDA
Cabeçalho com `row_count` e `limit` + tabela mascarada das linhas.

## NÃO FAÇA
- Não remova o TOP/limit.
- Não desabilite timeouts.
- Não exiba CPF, CNPJ, email, telefone, nome, endereço, token ou senha brutos.
