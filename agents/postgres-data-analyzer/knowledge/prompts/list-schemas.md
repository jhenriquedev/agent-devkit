# Prompt: list-schemas

> Operação read-only. Separe dados coletados de inferências.

## Objetivo
Listar os schemas disponíveis no banco alvo (excluindo schemas do sistema pg_*)
para orientar navegação de tabelas.

## Entradas esperadas
- `database` (opcional): nome do banco a inspecionar.

## Passos de raciocínio
1. Execute `list-schemas`.
2. Leia `count` e a lista `schemas`.
3. Apresente em tabela simples com `schema_name`.
4. Se o usuário mencionou um schema específico, confirme se ele aparece na lista.

## Regras de decisão
- Se schema solicitado não aparecer na lista, sinalize e sugira verificar permissões
  ou digitação. Não assuma que o schema existe.
- Schemas `pg_*` e `information_schema` são filtrados pelo runner — não mencione-os
  como ausentes por falha.

## Saída
Tabela markdown: `schema_name` + contagem total.

## NÃO faça
- Não liste tabelas ou colunas aqui.
- Não invente schemas não retornados.
