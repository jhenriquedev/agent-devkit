# Prompt: sample-table

> Operação read-only. Mascare PII. Limite explícito. Separe dados de inferências.

## Objetivo
Obter amostra de linhas de uma tabela para inspeção visual rápida, com PII mascarada,
para entender o formato real dos dados.

## Entradas esperadas
- `schema` (obrigatório): schema da tabela.
- `table` (obrigatório): nome da tabela.
- `limit` (default 20).
- `database` (opcional).

## Passos de raciocínio
1. **Antes de exibir**: rode `detect-sensitive-columns` para a tabela alvo (ou consulte
   resultado recente) — identifique o que mascarar.
2. Execute `sample-table`.
3. Aplique mascaramento às colunas sensíveis (ver Regras abaixo).
4. Exiba amostra com contagem e limite.

## Regras de mascaramento
- `sensitive_kind` cpf/cnpj/document → **mascarar SEMPRE**.
- `sensitive_kind` email/phone/name/address/token/password → **mascarar/omitir**.
- Se coluna de senha ou token aparecer, omita-a completamente da tabela.

## Regras de decisão
- Limit padrão 20 linhas — suficiente para inspeção de formato.
- Se a tabela for muito grande, recomende `profile-table` em vez de amostra.

## Saída
```
# Postgres Table Sample
- Database: <db>
- Schema: <schema>
- Table: <table>
- Rows: N (limite: N)
```
Tabela markdown mascarada.

## NÃO faça
- Não exiba CPF/CNPJ/email completo.
- Não exiba senha ou token.
- Não ultrapasse o limite.
