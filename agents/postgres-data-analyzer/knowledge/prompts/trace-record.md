# Prompt: trace-record

> Operação read-only. Mascare PII. Separe dados coletados de inferências.

## Objetivo
Localizar um registro específico por chave e navegar seus relacionamentos (FKs)
para rastrear a linhagem do dado, com PII mascarada.

## Entradas esperadas
- `schema` (obrigatório).
- `table` (obrigatório).
- `key-column` (obrigatório): coluna de chave do registro.
- `key-value` (obrigatório): valor da chave.
- `database` (opcional).

## Passos de raciocínio
1. **Antes de exibir**: identifique colunas sensíveis da tabela (via `detect-sensitive-columns`
   ou conhecimento prévio) — decida o que mascarar.
2. Execute `trace-record`.
3. Exiba o registro base com PII mascarada.
4. Navegue pelos relacionamentos (FKs) para mostrar registros relacionados — também mascarados.

## Regras de mascaramento
- `sensitive_kind` cpf/cnpj/document → **mascarar SEMPRE**.
- `sensitive_kind` email/phone/name/address/token → **mascarar/omitir**.
- Se `key-column` for CPF/documento, mascare o `key-value` na exibição.

## Regras de decisão
- Se o registro não for encontrado, informe claramente — não assuma que está em outra tabela.
- Relacionamentos navegados são baseados em FKs reais — informe quantos FKs foram seguidos.

## Saída
```
# Postgres Record Trace
- Database: <db>
- Tabela: schema.table
- Chave: key_column = <key_value mascarado se PII>
```
Registro base mascarado + seção de registros relacionados mascarados.

## NÃO faça
- Não exiba CPF/CNPJ completo, nem como key-value.
- Não navegue relacionamentos heurísticos — só FKs reais.
