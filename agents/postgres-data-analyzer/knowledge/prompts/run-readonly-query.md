# Prompt: run-readonly-query

> Operação read-only. Mascare PII. Nunca ultrapasse o limite. Separe dados de inferências.

## Objetivo
Executar uma query SELECT/WITH/EXPLAIN no banco com limite explícito e exibir
resultados com PII mascarada.

## Entradas esperadas
- `query` (obrigatório): query read-only validada.
- `limit` (default 100).
- `database` (opcional).

## Passos de raciocínio
1. **Antes de executar**: se a tabela alvo for desconhecida, rode `detect-sensitive-columns`
   para identificar o que mascarar.
2. Confirme que a query começa com SELECT/WITH/EXPLAIN. Se não, use `validate-readonly-query`.
3. Execute `run-readonly-query`.
4. Mascare colunas sensíveis na exibição (ver Regras de mascaramento abaixo).
5. Exiba resultado com contagem de linhas e limite aplicado.

## Regras de mascaramento
- `sensitive_kind` cpf/cnpj/document → **mascarar SEMPRE** (ex: `123.***.***-09`).
- `sensitive_kind` email/phone/name/address/token/password → **mascarar/omitir quando viável**.
- Se coluna não essencial à análise for sensível, omita-a da tabela exibida.

## Regras de decisão
- Query com keyword bloqueada → recuse e use `validate-readonly-query` primeiro.
- Timeout/erro de identificador → reduza limit ou especifique colunas; reexecute uma vez.
- Nunca ultrapasse o limit configurado.

## Saída
```
# Postgres Readonly Query
- Database: <db>
- Rows: N
- Limit: N
```
Tabela markdown com linhas mascaradas.

## NÃO faça
- Não exiba CPF/CNPJ completo.
- Não exiba senha, token ou hash de senha.
- Não ultrapasse o limite de linhas.
