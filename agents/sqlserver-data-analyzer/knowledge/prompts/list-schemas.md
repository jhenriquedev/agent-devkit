# Prompt: list-schemas

## OBJETIVO
Listar os schemas disponíveis no banco ativo (excluindo `sys` e
`INFORMATION_SCHEMA`).

## ENTRADAS
Nenhuma obrigatória. `database` é opcional (para mudar de banco).

## RACIOCÍNIO (passos)
1. Execute a capability `list-schemas`.
2. Leia `count` e `schemas[]` (campo: `schema_name`).
3. Destaque schemas com prefixo de domínio óbvio (ex.: `Sales`, `HumanResources`).

## RUBRICA / REGRAS DE DECISÃO
- Se `count == 1` e o schema é `dbo`, banco provavelmente não usa separação de
  schemas — sugira ir direto a `list-tables`.
- Se houver vários schemas, sugira o usuário escolher o schema alvo antes de
  consultar.

## SAÍDA
Tabela com `schema_name` + contagem total.

## NÃO FAÇA
- Não inclua schemas de sistema (`sys`, `INFORMATION_SCHEMA`, `guest`).
- Não infira propriedade ou permissões de schemas não explorados.
